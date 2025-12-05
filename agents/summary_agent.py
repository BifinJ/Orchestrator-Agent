from .base_agent import BaseAgent
import json, re
from datetime import datetime, timedelta
from statistics import mean
import google.generativeai as genai
from dotenv import load_dotenv
import os
from dateutil import parser
import re
from datetime import timedelta
from statistics import mean

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

class SummaryAgent(BaseAgent):
    def __init__(self, name="Summary Agent"):
        super().__init__(name)
        with open("data/logs/logs.json", "r") as f:
            self.logs = json.load(f)

        genai.configure(api_key=GOOGLE_API_KEY)

        self.llm = genai.GenerativeModel("gemini-2.0-flash-lite")


    def parse_date_query(self, query: str):
        """Extract start and end dates from user query dynamically"""
        now = datetime.now()
        start, end = None, now
        q = query.lower()

        # 1️⃣ Explicit date range like "from 10/12/2024 to 20/02/2025"
        range_match = re.search(
            r"from\s+([\w\s/-]+)\s+(?:to|until)\s+([\w\s/-]+)", query, re.IGNORECASE
        )
        if range_match:
            start = self.try_parse_date(range_match.group(1))
            end = self.try_parse_date(range_match.group(2))
            if start and end:
                return start, end

        # 2️⃣ Numeric or textual relative time: e.g., "last 3 months", "past 45 days", "previous year"
        num_match = re.search(r"(last|past|previous)\s+(\d+)?\s*(day|week|month|year)s?", query)
        if num_match:
            num = int(num_match.group(2)) if num_match.group(2) else 1
            unit = num_match.group(3)
            if "day" in unit:
                start = now - timedelta(days=num)
            elif "week" in unit:
                start = now - timedelta(weeks=num)
            elif "month" in unit:
                start = now - timedelta(days=30 * num)
            elif "year" in unit:
                start = now - timedelta(days=365 * num)
            return start, end

        # 3️⃣ Specific single dates like "01-10-2025", "2025/10/01", "Oct 15 2025"
        date_match = re.search(r"(\d{1,4}[-/]\d{1,2}[-/]\d{1,4}|\w{3,9}\s\d{1,2},?\s\d{4})", query)
        if date_match:
            single_date = self.try_parse_date(date_match.group(1))
            if single_date:
                start = single_date.replace(hour=0, minute=0, second=0)
                end = single_date.replace(hour=23, minute=59, second=59)
                return start, end

        # 4️⃣ Words like “today”, “yesterday”, “this week”, “last month”, etc.
        if any(k in q for k in ["today", "current day"]):
            start = now.replace(hour=0, minute=0, second=0)
            end = now
        elif any(k in q for k in ["yesterday", "previous day", "last day"]):
            start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0)
            end = (now - timedelta(days=1)).replace(hour=23, minute=59, second=59)
        elif any(k in q for k in ["last week", "previous week", "past week", "this week"]):
            start = now - timedelta(days=7)
        elif any(k in q for k in ["last month", "previous month", "past month", "this month"]):
            start = now - timedelta(days=30)
        elif any(k in q for k in ["last year", "previous year", "past year", "this year"]):
            start = now - timedelta(days=365)
        else:
            # fallback: include all logs
            start = datetime.min
        print("paesed date", start, end)
        return start, end

    def try_parse_date(self, date_str):
        """Try multiple formats and fallback to dateutil parser for textual dates"""
        for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%m-%d-%Y"):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        # fallback to dateutil parser for textual dates like 'Oct 15 2025'
        try:
            return parser.parse(date_str, dayfirst=True)
        except (ValueError, OverflowError):
            return None



    def filter_logs(self, start: datetime, end: datetime):
        logs = []
        for l in self.logs:
            if isinstance(l["date"], str):
                l["date"] = datetime.strptime(l["date"], "%Y-%m-%d")
            if start <= l["date"] <= end:
                logs.append(l)
        return logs
    
    
    def process(self, query: str) -> str:
        start, end = self.parse_date_query(query)
        filtered = self.filter_logs(start, end)
    
        if not filtered:
            return "No logs found for the requested period."
    
        # ✅ Sort logs by date
        filtered.sort(key=lambda x: x["date"])
    
        # ✅ Detect missing days in the log period
        all_dates = [log["date"] for log in filtered]
        missing_dates = []
        current_date = filtered[0]["date"]
        while current_date <= filtered[-1]["date"]:
            if current_date not in all_dates:
                missing_dates.append(current_date.strftime("%Y-%m-%d"))
            current_date += timedelta(days=1)
    
        # ✅ Handle missing logs gracefully
        total_days_expected = (filtered[-1]["date"] - filtered[0]["date"]).days + 1
        coverage_ratio = len(filtered) / total_days_expected * 100
    
        # ✅ Precompute accurate metrics
        avg_uptime = mean([l["uptime"] for l in filtered])
        avg_cost = mean([l["cost"] for l in filtered])
        avg_cpu = mean([l["cpu_usage"] for l in filtered])
        avg_memory = mean([l["memory_usage"] for l in filtered])
    
        total_cost = sum([l["cost"] for l in filtered])
        start_date = filtered[0]["date"].strftime("%Y-%m-%d")
        end_date = filtered[-1]["date"].strftime("%Y-%m-%d")
    
        # ✅ Compute trends
        def trend(field):
            start_val, end_val = filtered[0][field], filtered[-1][field]
            if end_val > start_val: return "increased"
            elif end_val < start_val: return "decreased"
            return "remained stable"
    
        trends = {
            "uptime_trend": trend("uptime"),
            "cost_trend": trend("cost"),
            "cpu_trend": trend("cpu_usage"),
            "memory_trend": trend("memory_usage"),
        }
    
        # ✅ Precomputed structured summary
        precomputed_summary = {
            "period": f"{start_date} to {end_date}",
            "total_days_expected": total_days_expected,
            "total_days_logged": len(filtered),
            "data_coverage": f"{coverage_ratio:.2f}%",
            "missing_days": missing_dates,
            "total_cost": round(total_cost, 2),
            "avg_uptime": round(avg_uptime, 2),
            "avg_cost": round(avg_cost, 2),
            "avg_cpu_usage": round(avg_cpu, 2),
            "avg_memory_usage": round(avg_memory, 2),
            **trends
        }
    
        # ✅ Logs to readable format for LLM context
        log_texts = [
            f"Date: {l['date'].strftime('%Y-%m-%d')}, Uptime: {l['uptime']}%, Cost: ${l['cost']}, "
            f"CPU: {l['cpu_usage']}%, Memory: {l['memory_usage']}%, Region: {l['region']}"
            for l in filtered
        ]
        logs_str = "\n".join(log_texts)
    
        # ✅ LLM prompt for natural summary
        prompt = (
            f"You are a cloud performance summary agent.\n"
            f"Here are verified metrics (computed by system):\n"
            f"{json.dumps(precomputed_summary, indent=2)}\n\n"
            f"Logs:\n{logs_str}\n\n"
            f"Missing log days: {len(missing_dates)} "
            f"({', '.join(missing_dates[:5]) + ('...' if len(missing_dates) > 5 else '')})\n\n"
            f"Create a concise, human-readable summary for '{query}'. "
            f"Highlight uptime, cost, and performance trends, note missing logs, "
            f"and suggest next steps for optimization. Do not modify numerical values."
        )
    
        summary = self.llm.generate_content(prompt)
        return summary.text
    