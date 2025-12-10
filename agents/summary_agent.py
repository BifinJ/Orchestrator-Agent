# agents/summary_agent.py
from .base_agent import BaseAgent
import os
import json
import re
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv

# date parsing: prefer dateparser for robust natural language parsing; fallback to dateutil
try:
    import dateparser
    DATEPARSER_AVAILABLE = True
except Exception:
    from dateutil import parser as dateutil_parser  # type: ignore
    DATEPARSER_AVAILABLE = False

# Gemini client (genai). Use tolerant import & client creation to handle SDK differences.
try:
    import genai  # type: ignore
    GENAI_AVAILABLE = True
except Exception:
    genai = None
    GENAI_AVAILABLE = False

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class SummaryAgent(BaseAgent):
    def __init__(self, name: str = "Summary Agent"):
        super().__init__(name)

        # File locations (as you provided)
        self.monitor_log_path = "logs/monitor_logs.log"
        self.metrics_history_path = "metrics/metrics_history.log"
        self.log_alerts_path = "storage/log_alerts.json"
        self.metric_alerts_path = "storage/metric_alerts.json"

        # LLM client initialization (tolerant)
        self.llm_client = None
        self.llm_model = "gemini-2.5-flash-lite"
        if GENAI_AVAILABLE and GEMINI_API_KEY:
            try:
                # Preferred modern client
                try:
                    self.llm_client = genai.Client(api_key=GEMINI_API_KEY)
                except Exception:
                    # Older SDK shape
                    try:
                        genai.configure(api_key=GEMINI_API_KEY)  # some installs support this
                        self.llm_client = genai
                    except Exception:
                        self.llm_client = None
            except Exception:
                self.llm_client = None

    # -------------------------
    # Date/time parsing helpers
    # -------------------------
    def _safe_parse_datetime(self, text: str) -> Optional[datetime]:
        if not text:
            return None
        text = str(text).strip()
        if DATEPARSER_AVAILABLE:
            try:
                dt = dateparser.parse(text, settings={"RETURN_AS_TIMEZONE_AWARE": True, "TO_TIMEZONE": "UTC"})
                return dt
            except Exception:
                return None
        else:
            try:
                dt = dateutil_parser.parse(text, fuzzy=True)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                else:
                    dt = dt.astimezone(timezone.utc)
                return dt
            except Exception:
                return None

    def parse_time_range(self, query: str) -> Tuple[datetime, datetime]:
        now = datetime.now(timezone.utc)
        q = (query or "").strip().lower()

        # 1) explicit range e.g. "from X to Y" or "between X and Y"
        m = re.search(r"(?:from|between)\s+(.+?)\s+(?:to|and)\s+(.+)", q)
        if m:
            left, right = m.group(1).strip(), m.group(2).strip()
            dt_left = self._safe_parse_datetime(left)
            dt_right = self._safe_parse_datetime(right)
            if dt_left and dt_right:
                # Expand to day boundaries if time not provided
                if dt_left.time() == datetime.min.time():
                    dt_left = dt_left.replace(hour=0, minute=0, second=0, microsecond=0)
                if dt_right.time() == datetime.min.time():
                    dt_right = dt_right.replace(hour=23, minute=59, second=59, microsecond=999999)
                return dt_left.astimezone(timezone.utc), dt_right.astimezone(timezone.utc)

        # 2) relative keywords
        if "day before yesterday" in q:
            start = (now - timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1, microseconds=-1)
            return start, end

        if "yesterday" in q:
            start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1, microseconds=-1)
            return start, end

        if "today" in q:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
            return start, end

        if "last week" in q or "past week" in q:
            start = (now - timedelta(weeks=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            return start, now

        if "last month" in q or "past month" in q:
            start = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
            return start, now

        # "past N days/weeks/months/years"
        m = re.search(r"past\s+(\d+)\s+(day|days|week|weeks|month|months|year|years)", q)
        if m:
            n = int(m.group(1))
            unit = m.group(2)
            if "day" in unit:
                start = now - timedelta(days=n)
            elif "week" in unit:
                start = now - timedelta(weeks=n)
            elif "month" in unit:
                start = now - timedelta(days=30 * n)
            elif "year" in unit:
                start = now - timedelta(days=365 * n)
            else:
                start = now - timedelta(days=n)
            return start, now

        # 3) try parse a single explicit date/time
        dt = self._safe_parse_datetime(query)
        if dt:
            # if only date given (time midnight) treat as whole day
            if dt.time() == datetime.min.time():
                start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
                end = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            else:
                start = dt
                end = dt
            return start.astimezone(timezone.utc), end.astimezone(timezone.utc)

        # 4) default: last 24 hours
        return (now - timedelta(days=1)), now

    # -------------------------
    # File loaders & normalizers
    # -------------------------
    def _read_lines_file(self, path: str) -> List[str]:
        if not os.path.exists(path):
            return []
        out = []
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                ln = line.strip()
                if ln:
                    out.append(ln)
        return out

    def _read_json_lines(self, path: str) -> List[Dict]:
        if not os.path.exists(path):
            return []
        rows = []
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        rows.append(obj)
                    elif isinstance(obj, list):
                        # if line itself is a list, extend
                        for el in obj:
                            if isinstance(el, dict):
                                rows.append(el)
                except Exception:
                    # If file is full JSON array rather than ndjson
                    try:
                        f.seek(0)
                        data = json.load(f)
                        if isinstance(data, dict):
                            rows.append(data)
                        elif isinstance(data, list):
                            for el in data:
                                if isinstance(el, dict):
                                    rows.append(el)
                        break
                    except Exception:
                        # give up on this line
                        continue
        return rows

    def _read_alert_file(self, path: str) -> List[Dict]:
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
            flat = []
            if isinstance(data, dict):
                flat.append(data)
            elif isinstance(data, list):
                # flatten nested lists/dicts
                for item in data:
                    if isinstance(item, dict):
                        flat.append(item)
                    elif isinstance(item, list):
                        for sub in item:
                            if isinstance(sub, dict):
                                flat.append(sub)
            return flat
        except Exception:
            # fallback to line-by-line parse
            return self._read_json_lines(path)

    # -------------------------
    # Time-based filters
    # -------------------------
    def _filter_logs_by_time(self, lines: List[str], start: datetime, end: datetime) -> List[str]:
        out = []
        for ln in lines:
            # logs begin with a timestamp token — try first token, fallback to ISO regex
            parts = ln.split()
            if not parts:
                continue
            ts_token = parts[0]
            ts = self._safe_parse_datetime(ts_token)
            if ts is None:
                # attempt to find an ISO-like timestamp in entire line
                m = re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+\d{2}:\d{2})?", ln)
                if m:
                    ts = self._safe_parse_datetime(m.group(0))
            if ts is None:
                continue
            if start <= ts <= end:
                out.append(ln)
        return out

    def _filter_metrics_by_time(self, rows: List[Dict], start: datetime, end: datetime) -> List[Dict]:
        out = []
        for r in rows:
            ts_str = r.get("timestamp") or r.get("time") or r.get("ts")
            ts = self._safe_parse_datetime(ts_str) if ts_str else None
            if ts is None:
                continue
            if start <= ts <= end:
                out.append(r)
        return out

    def _filter_alerts_by_time(self, alerts: List[Dict], start: datetime, end: datetime) -> List[Dict]:
        # alerts may already be normalized; ensure it's a flat list of dicts
        flat = []
        for a in alerts:
            if isinstance(a, dict):
                flat.append(a)
            elif isinstance(a, list):
                for sub in a:
                    if isinstance(sub, dict):
                        flat.append(sub)
        out = []
        for a in flat:
            ts_str = a.get("timestamp")
            if not ts_str:
                continue
            ts = self._safe_parse_datetime(ts_str)
            if ts is None:
                continue
            if start <= ts <= end:
                out.append(a)
        return out

    # -------------------------
    # Analysis helpers
    # -------------------------
    def _analyze_logs(self, logs: List[str]) -> Dict:
        total = len(logs)
        error_count = 0
        warn_count = 0
        status_counts: Dict[str, int] = {}
        examples: List[str] = []
        success_count = 0

        status_re = re.compile(r"\b(2\d{2}|3\d{2}|4\d{2}|5\d{2})\b")
        for ln in logs:
            low = ln.lower()
            if any(k in low for k in ("error", "exception", "traceback", "fatal")):
                error_count += 1
                if len(examples) < 3:
                    examples.append(ln)
            if "warn" in low or "warning" in low:
                warn_count += 1
            m = status_re.search(ln)
            if m:
                code = m.group(1)
                status_counts[code] = status_counts.get(code, 0) + 1
                if code.startswith("2") or code.startswith("3"):
                    success_count += 1
            else:
                if re.search(r"\b(success|ok|completed)\b", ln, flags=re.I):
                    success_count += 1

        estimated_success_rate = None
        denom = success_count + error_count
        if denom > 0:
            estimated_success_rate = (success_count / denom) * 100.0

        return {
            "total_lines": total,
            "error_count": error_count,
            "warn_count": warn_count,
            "status_counts": status_counts,
            "examples": examples,
            "estimated_success_rate_percent": estimated_success_rate,
        }

    def _analyze_metrics(self, metrics: List[Dict]) -> Dict:
        import math, statistics

        def numeric_list(key):
            vals = []
            for m in metrics:
                v = m.get(key)
                if v is None:
                    continue
                try:
                    vals.append(float(v))
                except Exception:
                    continue
            return vals

        cpu = numeric_list("CPU_Usage")
        memory = numeric_list("Memory_Usage")
        db_conn = numeric_list("DB_Connections")
        req_rate = numeric_list("Request_Rate")

        def summarise(vals):
            if not vals:
                return None
            try:
                return {
                    "count": len(vals),
                    "avg": statistics.mean(vals),
                    "min": min(vals),
                    "max": max(vals),
                    "median": statistics.median(vals),
                }
            except Exception:
                return None

        cpu_summary = summarise(cpu)
        mem_summary = summarise(memory)
        db_summary = summarise(db_conn)
        req_summary = summarise(req_rate)

        # simple spike detection using z-score threshold 2.5
        spikes = []
        if cpu and len(cpu) >= 3:
            mean = statistics.mean(cpu)
            stdev = statistics.pstdev(cpu)
            if stdev > 0:
                for i, v in enumerate(cpu):
                    z = (v - mean) / stdev
                    if abs(z) >= 2.5:
                        spikes.append({"index": i, "value": v, "z": z})

        return {
            "cpu": cpu_summary,
            "memory": mem_summary,
            "db_connections": db_summary,
            "request_rate": req_summary,
            "cpu_spikes_count": len(spikes),
            "cpu_spike_examples": spikes[:3],
        }

    # -------------------------
    # LLM prompt and call
    # -------------------------
    def _build_prompt(self, query: str, start: datetime, end: datetime,
                      logs: List[str], metrics: List[Dict],
                      log_alerts: List[Dict], metric_alerts: List[Dict],
                      log_stats: Dict, metric_stats: Dict) -> str:
        # compact examples to include
        log_examples = logs[:5]
        metric_examples = metrics[:10]

        prompt = (
            f"System monitoring summary request.\n"
            f"User query: {query}\n"
            f"Time window: {start.isoformat()} to {end.isoformat()}\n\n"
            f"Key metrics summary (computed): {json.dumps(metric_stats, default=str)}\n"
            f"Key log summary (computed): {json.dumps(log_stats, default=str)}\n\n"
            f"Log anomalies (matched alerts): {json.dumps(log_alerts, default=str)}\n"
            f"Metric anomalies (matched alerts): {json.dumps(metric_alerts, default=str)}\n\n"
            f"Example log lines (up to 5):\n{json.dumps(log_examples, indent=2)}\n\n"
            f"Example metric samples (up to 10):\n{json.dumps(metric_examples, indent=2)}\n\n"
            "Please produce a single concise paragraph (one paragraph only) that:\n"
            "- Summarizes the overall activity and health in the window.\n"
            "- Prioritizes errors and anomalies and notes they were forwarded to remediation agent (do not describe remediation steps).\n"
            "- Includes estimated API call success rate if available, average CPU and memory, number of CPU spikes, and notable HTTP status counts.\n"
            "- If no anomalies, state the system appears stable and provide the main metrics.\n"
            "Keep the paragraph short and precise."
        )
        return prompt

    def _call_llm(self, prompt: str) -> Optional[str]:
        if not self.llm_client:
            return None
        try:
            # Try common modern interface
            try:
                resp = self.llm_client.models.generate_content(model=self.llm_model, contents=prompt)
                # extract text safely
                if hasattr(resp, "text"):
                    return resp.text
                # try dict-style
                if isinstance(resp, dict):
                    cand = resp.get("candidates") or resp.get("outputs")
                    if cand and isinstance(cand, list) and len(cand) > 0:
                        first = cand[0]
                        if isinstance(first, dict):
                            return first.get("content") or first.get("text") or str(first)
                        return str(first)
                    return str(resp)
            except Exception:
                # try alternative older interface
                try:
                    resp2 = self.llm_client.generate_text(model=self.llm_model, prompt=prompt)
                    if hasattr(resp2, "text"):
                        return resp2.text
                    return str(resp2)
                except Exception:
                    return None
        except Exception:
            return None

    # -------------------------
    # Local deterministic one-paragraph summary fallback
    # -------------------------
    def _local_summary(self, query: str, start: datetime, end: datetime,
                       logs: List[str], metrics: List[Dict],
                       log_alerts: List[Dict], metric_alerts: List[Dict]) -> str:
        log_stats = self._analyze_logs(logs)
        metric_stats = self._analyze_metrics(metrics)

        parts = [f"Between {start.isoformat()} and {end.isoformat()}"]

        if log_stats["total_lines"] == 0:
            parts.append("no log entries were recorded")
        else:
            parts.append(f"{log_stats['total_lines']} log lines recorded with {log_stats['error_count']} errors and {log_stats['warn_count']} warnings")
            if log_stats["estimated_success_rate_percent"] is not None:
                parts.append(f"estimated success rate {log_stats['estimated_success_rate_percent']:.0f}%")

        metric_parts = []
        if metric_stats["cpu"]:
            metric_parts.append(f"avg CPU {metric_stats['cpu']['avg']:.1f}% (max {metric_stats['cpu']['max']:.1f}%)")
        if metric_stats["memory"]:
            metric_parts.append(f"avg memory {metric_stats['memory']['avg']:.1f}%")
        if metric_stats["db_connections"]:
            metric_parts.append(f"avg DB connections {metric_stats['db_connections']['avg']:.1f}")
        if metric_parts:
            parts.append("metrics: " + ", ".join(metric_parts))

        if metric_stats["cpu_spikes_count"] > 0:
            parts.append(f"{metric_stats['cpu_spikes_count']} CPU spike(s) detected")

        if log_alerts:
            parts.append(f"{len(log_alerts)} log anomaly(ies) forwarded to remediation")
        if metric_alerts:
            parts.append(f"{len(metric_alerts)} metric anomaly(ies) forwarded to remediation")

        # notable status codes
        sc = log_stats.get("status_counts", {})
        if sc:
            top = sorted(sc.items(), key=lambda kv: kv[1], reverse=True)[:2]
            parts.append("notable HTTP statuses: " + ", ".join(f"{k} x{v}" for k, v in top))

        paragraph = "; ".join(parts) + "."
        paragraph = paragraph[0].upper() + paragraph[1:]
        return paragraph

    # -------------------------
    # Public process() method
    # -------------------------
    def process(self, query: str) -> str:
        start, end = self.parse_time_range(query)

        # load raw data
        raw_logs = self._read_lines_file(self.monitor_log_path)
        raw_metrics = self._read_json_lines(self.metrics_history_path)
        raw_log_alerts = self._read_alert_file(self.log_alerts_path)
        raw_metric_alerts = self._read_alert_file(self.metric_alerts_path)

        # filter by time
        logs = self._filter_logs_by_time(raw_logs, start, end)
        metrics = self._filter_metrics_by_time(raw_metrics, start, end)
        log_alerts = self._filter_alerts_by_time(raw_log_alerts, start, end)
        metric_alerts = self._filter_alerts_by_time(raw_metric_alerts, start, end)

        # compute brief stats for prompt
        log_stats = self._analyze_logs(logs)
        metric_stats = self._analyze_metrics(metrics)

        # build LLM prompt
        prompt = self._build_prompt(query, start, end, logs, metrics, log_alerts, metric_alerts, log_stats, metric_stats)

        # call LLM
        llm_out = self._call_llm(prompt)
        if llm_out:
            # convert multi-line to single paragraph
            lines = [ln.strip() for ln in llm_out.strip().splitlines() if ln.strip()]
            one_par = " ".join(lines)
            # extra safety: if very long, keep first paragraph
            if "\n\n" in one_par:
                one_par = one_par.split("\n\n", 1)[0].replace("\n", " ")
            return one_par

        # fallback deterministic summary
        return self._local_summary(query, start, end, logs, metrics, log_alerts, metric_alerts)
