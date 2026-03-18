# agents/summary_agent.py
import os
import json
import re
import statistics
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
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

        # Existing sources
        self.monitor_log_path = "logs/monitor_logs.log"
        self.metrics_history_path = "metrics/metrics_history.log"
        self.log_alerts_path = "storage/log_alerts.json"
        self.metric_alerts_path = "storage/metric_alerts.json"

        # NEW sources
        self.knowledge_base_path = "storage/knowledge_base.jsonl"
        self.diagnosis_logs_path = "storage/diagnosis_logs.jsonl"
        self.action_stats_path = "storage/action_stats.json"
        self.approval_path = "storage/approval.json"

        self.model = None
        if GENAI_AVAILABLE and GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                models = [
                    m.name for m in genai.list_models()
                    if 'generateContent' in m.supported_generation_methods
                ]
                target = next(
                    (m for m in models if "gemini-1.5-flash" in m),
                    models[0]
                )
                self.model = genai.GenerativeModel(target)
            except Exception as e:
                print(f"[DEBUG] LLM Setup Error: {e}")

    async def run(self, query: str, context: dict = None):
        now = datetime.now(timezone.utc)
        start = (
            now.replace(day=1, hour=0, minute=0)
            if "month" in query.lower()
            else (now - timedelta(days=1))
        )

        # Core data
        logs = self._get_data(self.monitor_log_path, start, now, is_json=False)
        metrics = self._get_data(self.metrics_history_path, start, now, is_json=True)
        alerts = self._read_json_list(self.log_alerts_path) + self._read_json_list(self.metric_alerts_path)

        # NEW data
        knowledge_logs = self._read_jsonl(self.knowledge_base_path, start, now)
        diagnosis_logs = self._read_jsonl(self.diagnosis_logs_path, start, now)

        # Optional (only if asked)
        include_action_stats = "action stats" in query.lower()
        include_approval = "approval" in query.lower()

        action_stats = self._read_json_file(self.action_stats_path) if include_action_stats else {}
        approval_stats = self._read_json_file(self.approval_path) if include_approval else {}

        # Analyze
        metric_stats = self._analyze_metrics(metrics)
        knowledge_stats = self._analyze_knowledge_logs(knowledge_logs)
        diagnosis_stats = self._analyze_diagnosis_logs(diagnosis_logs)

        # Build context
        context = {
            "query": query,
            "period": f"{start.date()} to {now.date()}",

            "log_count": len(logs),
            "recent_logs": logs[-15:],
            "metric_stats": metric_stats,

            "remediation_count": len(knowledge_logs),

            "knowledge_stats": knowledge_stats,
            "diagnosis_stats": diagnosis_stats,

            "action_stats": action_stats,
            "approval_stats": approval_stats
        }

        prompt = f"""
        System Data:
        {json.dumps(context, indent=2, default=str)}
        
        User Query: "{query}"
        
        Instructions:
        1. Act as a precise monitoring bot.
        2. Use short, declarative sentences.
        3. Report error codes or keywords from logs.
        4. Include:
           - Peak CPU
           - Remediation count
           - Diagnosis count
           - Success rate of actions
        5. Mention most frequent root cause and action.
        6. If missing data: "Data not available for [item]".
        7. Length: 80–100 words.
        """

        if self.model:
            try:
                response = self.model.generate_content(prompt)
                return response.text.strip()
            except Exception:
                pass

        # Fallback (rule-based)
        return self._fallback_summary(context)

    # =========================
    # DATA READERS
    # =========================

    def _get_data(self, path, start, end, is_json=False):
        if not os.path.exists(path):
            return []

        results = []
        with open(path, "r") as f:
            for line in f:
                try:
                    ts_match = re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", line)
                    if not ts_match:
                        continue

                    ts = datetime.fromisoformat(ts_match.group(0)).replace(tzinfo=timezone.utc)

                    if start <= ts <= end:
                        results.append(json.loads(line) if is_json else line.strip())
                except:
                    continue

        return results

    def _read_jsonl(self, path, start, end):
        if not os.path.exists(path):
            return []

        results = []
        with open(path, "r") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    ts = datetime.fromisoformat(obj["timestamp"].replace("Z", "+00:00"))
                    if start <= ts <= end:
                        results.append(obj)
                except:
                    continue

        return results

    def _read_json_list(self, path):
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r") as f:
                data = json.load(f)
                return data if isinstance(data, list) else [data]
        except:
            return []

    def _read_json_file(self, path):
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r") as f:
                return json.load(f)
        except:
            return {}

    # =========================
    # ANALYSIS
    # =========================

    def _analyze_metrics(self, metrics):
        cpu = [float(m['value']) for m in metrics if m.get('metric') == 'CPUUtilization']
        return {
            "avg_cpu": f"{statistics.mean(cpu):.1f}%" if cpu else "N/A",
            "peak_cpu": f"{max(cpu):.1f}%" if cpu else "N/A"
        }

    def _analyze_knowledge_logs(self, logs):
        if not logs:
            return {}

        success = [l for l in logs if l.get("success") is True]
        failure = [l for l in logs if l.get("success") is False]

        actions = {}
        for l in logs:
            a = l.get("action")
            if a:
                actions[a] = actions.get(a, 0) + 1

        return {
            "total": len(logs),
            "success_rate": round(len(success) / len(logs), 2) if logs else 0,
            "top_action": max(actions, key=actions.get) if actions else None
        }

    def _analyze_diagnosis_logs(self, logs):
        if not logs:
            return {}

        root_causes = {}
        for l in logs:
            rc = l.get("root_cause")
            if rc:
                root_causes[rc] = root_causes.get(rc, 0) + 1

        return {
            "total": len(logs),
            "top_root_cause": max(root_causes, key=root_causes.get) if root_causes else None
        }

    # =========================
    # FALLBACK
    # =========================

    def _fallback_summary(self, context):
        return (
            f"Logs analyzed: {context['log_count']}. "
            f"Peak CPU: {context['metric_stats']['peak_cpu']}. "
            f"Remediations: {context['remediation_count']}. "
            f"Diagnoses: {context['diagnosis_stats'].get('total', 'N/A')}. "
            f"Top root cause: {context['diagnosis_stats'].get('top_root_cause', 'N/A')}. "
            f"Action success rate: {context['knowledge_stats'].get('success_rate', 'N/A')}."
        )