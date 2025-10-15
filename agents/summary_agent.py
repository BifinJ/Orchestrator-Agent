from .base_agent import BaseAgent
import json, re
from datetime import datetime, timedelta
from statistics import mean
import google.generativeai as genai
from dotenv import load_dotenv
import os
from dateutil import parser
import re

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

        # Prepare logs in readable format
        log_texts = []
        for l in filtered:
            log_texts.append(
                f"Date: {l['date'].strftime('%Y-%m-%d')}, "
                f"Uptime: {l['uptime']}%, "
                f"Cost: ${l['cost']}, "
                f"CPU: {l['cpu_usage']}%, "
                f"Memory: {l['memory_usage']}%, "
                f"Region: {l['region']}"
            )

        logs_str = "\n".join(log_texts)

        # Create prompt for Gemini
        prompt = (
            f"Summarize the following cloud logs for the user query '{query}':\n"
            f"{logs_str}\n"
            f"Provide insights such as trends, unusual spikes, or cost optimization opportunities, "
            f"in a concise, natural paragraph."
        )

        # Send prompt to Gemini
        summary = self.llm.generate_content(prompt)
        return summary.text
