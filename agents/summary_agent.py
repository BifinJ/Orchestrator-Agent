# agents/summary_agent.py
import os
import json
import re
import statistics
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv
from .base_agent import BaseAgent

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except Exception:
    genai = None
    GENAI_AVAILABLE = False

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class SummaryAgent(BaseAgent):
    def __init__(self, name: str = "Summary Agent"):
        super().__init__(name)
        self.monitor_log_path = "logs/monitor_logs.log"
        self.metrics_history_path = "metrics/metrics_history.log"
        self.log_alerts_path = "storage/log_alerts.json"
        self.metric_alerts_path = "storage/metric_alerts.json"
        
        self.model = None
        if GENAI_AVAILABLE and GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                # Dynamic discovery to prevent 404 errors
                models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                target = next((m for m in models if "gemini-1.5-flash" in m), models[0])
                self.model = genai.GenerativeModel(target)
            except Exception as e:
                print(f"[DEBUG] LLM Setup Error: {e}")

    async def run(self, query: str, context: dict = None):
        now = datetime.now(timezone.utc)
        start = now.replace(day=1, hour=0, minute=0) if "month" in query.lower() else (now - timedelta(days=1))
        
        logs = self._get_data(self.monitor_log_path, start, now, is_json=False)
        metrics = self._get_data(self.metrics_history_path, start, now, is_json=True)
        alerts = self._read_json_list(self.log_alerts_path) + self._read_json_list(self.metric_alerts_path)

        # Context provided to the LLM
        context = {
            "query": query,
            "period": f"{start.date()} to {now.date()}",
            "log_count": len(logs),
            "recent_logs": logs[-15:], 
            "metric_stats": self._analyze_metrics(metrics),
            "remediation_count": len(alerts)
        }

        # Refined Prompt for Bot-like, precise response
        prompt = f"""
        System Data:
        {json.dumps(context, indent=2, default=str)}
        
        User Query: "{query}"
        
        Instructions:
        1. Act as a precise monitoring bot. 
        2. Use short, declarative sentences. No conversational filler or "teammate" talk.
        3. Report specific error codes (e.g. 500, 404) or keywords found in 'recent_logs'.
        4. State the max CPU, network peaks, and remediation count.
        5. If data for a specific request (like 'users') is missing, state: "Data not available for [item]".
        6. Total length: 80-100 words.
        """

        if self.model:
            try:
                response = self.model.generate_content(prompt)
                return response.text.strip()
            except Exception:
                pass

        # Simple, non-formatted fallback
        return f"Summary: {len(logs)} logs and {len(metrics)} metrics analyzed. Errors found: {len(alerts)}. Peak CPU: {context['metric_stats']['peak_cpu']}. Success rate: {context['metric_stats'].get('api_success', 'N/A')}. {len(alerts)} remediations performed."

    def _get_data(self, path, start, end, is_json=False):
        if not os.path.exists(path): return []
        results = []
        with open(path, "r") as f:
            for line in f:
                try:
                    ts_match = re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", line)
                    if not ts_match: continue
                    ts = datetime.fromisoformat(ts_match.group(0)).replace(tzinfo=timezone.utc)
                    if start <= ts <= end:
                        results.append(json.loads(line) if is_json else line.strip())
                except: continue
        return results

    def _read_json_list(self, path):
        if not os.path.exists(path): return []
        try:
            with open(path, "r") as f:
                data = json.load(f)
                return data if isinstance(data, list) else [data]
        except: return []

    def _analyze_metrics(self, metrics):
        cpu = [float(m['value']) for m in metrics if m.get('metric') == 'CPUUtilization']
        return {
            "avg_cpu": f"{statistics.mean(cpu):.1f}%" if cpu else "N/A",
            "peak_cpu": f"{max(cpu):.1f}%" if cpu else "N/A"
        }