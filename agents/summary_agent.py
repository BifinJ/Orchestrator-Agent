import os
import json
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
import google.generativeai as genai

from .base_agent import BaseAgent

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class SummaryAgent(BaseAgent):
    def __init__(self, name="Summary Agent"):
        super().__init__(name)

        # -------- LOAD ALL DATA SOURCES --------
        self.monitor_log_path = "logs/monitor_logs.log"
        self.metrics_history_path = "metrics/metrics_history.log"
        self.log_alerts_path = "storage/log_alerts.json"
        self.metric_alerts_path = "storage/metric_alerts.json"

        # Init LLM
        genai.configure(api_key=GEMINI_API_KEY)
        self.llm = genai.GenerativeModel("gemini-2.5-flash-lite")

    # ---------------------------------------------------------------------
    # TIME RANGE PARSER – supports:
    # "yesterday", "last week", "last month",
    # "past n days", "past 3 weeks", "from dec 9 2025", "between X and Y"
    # ---------------------------------------------------------------------
    def parse_time_range(self, query: str):
        now = datetime.now()

        q = query.lower()

        # 1. Yesterday
        if "yesterday" in q:
            start = now - timedelta(days=1)
            end = now
            return start, end

        # 2. Day before yesterday
        if "day before yesterday" in q:
            start = now - timedelta(days=2)
            end = now - timedelta(days=1)
            return start, end

        # 3. Last week
        if "last week" in q:
            start = now - timedelta(weeks=1)
            end = now
            return start, end

        # 4. Last month
        if "last month" in q:
            start = now - relativedelta(months=1)
            end = now
            return start, end

        # 5. Past n days/weeks/months
        import re
        match = re.search(r"past (\d+) (day|days|week|weeks|month|months)", q)
        if match:
            n = int(match.group(1))
            unit = match.group(2)

            if "day" in unit:
                start = now - timedelta(days=n)
            elif "week" in unit:
                start = now - timedelta(weeks=n)
            elif "month" in unit:
                start = now - relativedelta(months=n)

            return start, now

        # 6. Explicit date e.g. "Dec 9 2025"
        try:
            parsed_date = date_parser.parse(query, fuzzy=True)
            start = parsed_date.replace(hour=0, minute=0, second=0)
            end = parsed_date.replace(hour=23, minute=59, second=59)
            return start, end
        except:
            pass

        # DEFAULT → last 24 hours
        return now - timedelta(days=1), now

    # ---------------------------------------------------------------------
    # LOAD AND FILTER LOGS
    # ---------------------------------------------------------------------
    def filter_logs(self, start: datetime, end: datetime):
        events = []

        if not os.path.exists(self.monitor_log_path):
            return []

        with open(self.monitor_log_path, "r") as f:
            for line in f:
                try:
                    parts = line.split(" ")
                    ts = date_parser.parse(parts[0])
                    if start <= ts <= end:
                        events.append(line.strip())
                except:
                    continue

        return events

    # ---------------------------------------------------------------------
    # LOAD AND FILTER METRICS HISTORY
    # ---------------------------------------------------------------------
    def filter_metrics(self, start: datetime, end: datetime):
        metrics = []

        if not os.path.exists(self.metrics_history_path):
            return []

        with open(self.metrics_history_path, "r") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    ts = date_parser.parse(data["timestamp"])
                    if start <= ts <= end:
                        metrics.append(data)
                except:
                    continue

        return metrics

    # ---------------------------------------------------------------------
    # FILTER ANOMALY ALERTS
    # ---------------------------------------------------------------------
    def filter_anomalies(self, start: datetime, end: datetime):

        log_alerts = []
        metric_alerts = []

        if os.path.exists(self.log_alerts_path):
            with open(self.log_alerts_path, "r") as f:
                try:
                    data = json.load(f)
                    # single object or list—normalize
                    if isinstance(data, dict):
                        data = [data]

                    for item in data:
                        ts = date_parser.parse(item["timestamp"])
                        if start <= ts <= end:
                            log_alerts.append(item)
                except:
                    pass

        if os.path.exists(self.metric_alerts_path):
            with open(self.metric_alerts_path, "r") as f:
                try:
                    data = json.load(f)
                    for item in data:
                        ts = date_parser.parse(item["timestamp"])
                        if start <= ts <= end:
                            metric_alerts.append(item)
                except:
                    pass

        return log_alerts, metric_alerts

    # ---------------------------------------------------------------------
    # MAIN PROCESS METHOD
    # ---------------------------------------------------------------------
    def process(self, query: str) -> str:

        # 1. Parse the time window
        start, end = self.parse_time_range(query)

        # 2. Retrieve logs and metrics
        logs = self.filter_logs(start, end)
        metrics = self.filter_metrics(start, end)
        log_anoms, metric_anoms = self.filter_anomalies(start, end)

        # 3. Prepare LLM prompt
        prompt = f"""
        You are a system monitoring summary agent.

        Summarize the system activity between:
        START: {start.isoformat()}
        END:   {end.isoformat()}

        User query: "{query}"

        Provide a **single, precise paragraph** focusing on:
        - Key events
        - Errors (these take priority)
        - Metrics patterns
        - Log anomalies
        - Metric anomalies

        DO NOT include remediation actions.

        ----------------------
        LOGS:
        {json.dumps(logs, indent=2)}

        METRICS:
        {json.dumps(metrics, indent=2)}

        LOG ANOMALIES:
        {json.dumps(log_anoms, indent=2)}

        METRIC ANOMALIES:
        {json.dumps(metric_anoms, indent=2)}
        ----------------------

        Produce a concise, coherent summary.
        """

        response = self.llm.generate_content(prompt)
        return response.text
