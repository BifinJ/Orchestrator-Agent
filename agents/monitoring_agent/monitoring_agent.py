import time
import threading
from datetime import datetime, timedelta, timezone
import os

from agents.base_agent import BaseAgent
from agents.monitoring_agent.aws_helper import logs_client, cw_client
from agents.monitoring_agent.metric_helper import rolling_zscore
from agents.monitoring_agent.storage_helper import append_json, append_metric, save_local_log
from agents.monitoring_agent.detection_helper import classify_log, detect_http_status
from agents.remediation_agent.remediation_agent import remediation_agent
from agents.diagnosis_agent.diagnostic_agent import DiagnosticAgent

from agents.diagnosis_agent.data_loader import load_metrics, load_logs


LOG_GROUP = os.getenv("LOG_GROUP")
INSTANCE_ID = os.getenv("INSTANCE_ID")

STATUS_ALERT_THRESHOLD = 4
STATUS_WINDOW_SECONDS = 120
ZSCORE_THRESHOLD = 2.5

metrics_l = load_metrics("metrics/metrics_history.log")
logs_l = load_logs("logs/monitor_logs.log")

diagnostic_agent = DiagnosticAgent(
    metrics=metrics_l,
    logs=logs_l 
)


class MonitoringAgent(BaseAgent):

    def __init__(self):
        super().__init__(
    name="MonitoringAgent",
    description="Monitors AWS EC2 logs and metrics, detects anomalies and triggers remediation"
)

        self.seen_logs = set()
        self.status_events = []
        self.metric_history = {}

    # ---------------- LOGS ----------------
    def poll_logs(self):
        print(f"[LOG] Monitoring {LOG_GROUP} and saving to local storage...")
        
        # Use milliseconds for AWS API
        self.last_log_ts = int((datetime.now(timezone.utc) - timedelta(minutes=5)).timestamp() * 1000)

        while True:
            try:
                next_token = None
                while True:
                    params = {
                        "logGroupName": LOG_GROUP,
                        "startTime": self.last_log_ts,
                        "interleaved": True
                    }
                    if next_token:
                        params["nextToken"] = next_token

                    resp = logs_client.filter_log_events(**params)
                    events = resp.get("events", [])

                    for ev in events:
                        # 1. Update timestamp tracker
                        self.last_log_ts = max(self.last_log_ts, ev["timestamp"] + 1)
                        
                        msg = ev["message"]
                        if not isinstance(msg, str):
                            continue

                        ts_ms = ev["timestamp"]
                        ts_iso = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).isoformat()

                        # 2. SAVE to local log file (as requested)
                        save_local_log(f"{ts_iso} {msg}")

                        # 3. CLASSIFY and alert if ERROR/WARN
                        category = classify_log(msg)
                        if category:
                            alert = {
    "type": category,
    "service": "api",
    "timestamp": ts_iso,
    "message": msg
}
                            


                            print(f"[ALERT] Detected :" , type(alert))
                            diagnosis = diagnostic_agent.handle_anomaly(alert)
                            print(f"[DIAGNOSIS] Results:", diagnosis)
                            append_json("storage/log_alerts.json", alert)

                            # if diagnosis:
                            #     remediation_agent({
                            #         "alert": alert,
                            #         "diagnosis": diagnosis
                            #     })


                        # 4. DETECT HTTP status codes (e.g., 404, 500)
                        status = detect_http_status(msg)
                        if status:
                            now = datetime.now(timezone.utc)
                            self.status_events.append((now, status))
                            # Keep only logs within the window
                            self.status_events = [
                                e for e in self.status_events
                                if e[0] > now - timedelta(seconds=STATUS_WINDOW_SECONDS)
                            ]
                            count = sum(1 for _, s in self.status_events if s == status)
                            if count >= STATUS_ALERT_THRESHOLD:
                                alert = {
    "type": "status_repeated",
    "service": "api",
    "timestamp": ts_iso,
    "status": status,
    "count": count
}

                                append_json("storage/log_alerts.json", alert)
                                diagnosis = diagnostic_agent.handle_anomaly(alert)
                                if diagnosis:
                                    remediation_agent({
                                        "alert": alert,
                                        "diagnosis": diagnosis
                                    })

                    next_token = resp.get("nextToken")
                    
                    # If we found events, we processed them, so wait for new ones.
                    # If no events but no token, we are at the "head" of the log, so wait.
                    if events or not next_token:
                        break

            except Exception as e:
                print(f"[ERR] log polling session: {e}")

            time.sleep(5)

    # ---------------- METRICS (LIVE, NO HARDCODING) ----------------

    def poll_metrics(self):
        print("[METRIC] Discovering live EC2 metrics from {INSTANCE_ID}...")
        while True:
            try:
                discovered = cw_client.list_metrics(
                    Dimensions=[{"Name": "InstanceId", "Value": INSTANCE_ID}]
                )["Metrics"]

                for m in discovered:
                    namespace = m["Namespace"]
                    metric_name = m["MetricName"]
                    dimensions = m["Dimensions"]

                    resp = cw_client.get_metric_statistics(
                        Namespace=namespace,
                        MetricName=metric_name,
                        Dimensions=dimensions,
                        StartTime=datetime.utcnow() - timedelta(minutes=5),
                        EndTime=datetime.utcnow(),
                        Period=60,
                        Statistics=["Average"]
                    )

                    datapoints = resp.get("Datapoints", [])
                    if not datapoints:
                        continue

                    latest = max(datapoints, key=lambda x: x["Timestamp"])
                    value = latest["Average"]
                    ts_iso = latest["Timestamp"].replace(
                        tzinfo=timezone.utc
                    ).isoformat()

                    # ---- STORE METRIC (PERSISTENT) ----
                    metric_record = {
                        "timestamp": ts_iso,
                        "namespace": namespace,
                        "metric": metric_name,
                        "value": value,
                        "dimensions": dimensions
                    }
                    append_metric(metric_record)

                    # ---- Z-SCORE DETECTION ----
                    self.metric_history.setdefault(metric_name, []).append(value)
                    zs = rolling_zscore(self.metric_history[metric_name])

                    if zs[-1] is not None and abs(zs[-1]) > ZSCORE_THRESHOLD:
                        alert = {
    "type": "metric_anomaly",
    "service": "api",
    "metric": metric_name,
    "namespace": namespace,
    "value": value,
    "zscore": float(zs[-1]),
    "timestamp": ts_iso
}

                        append_json("storage/metric_alerts.json", alert)

                        diagnosis = diagnostic_agent.handle_anomaly(alert)

                        if diagnosis:
                            remediation_agent({
                                "alert": alert,
                                "diagnosis": diagnosis
                            })


            except Exception as e:
                print("[ERR] metric polling:", e)

            time.sleep(20)

    async def run(self, message: str = "", context: dict = None):
        """
        Entry point for orchestrator / agent runtime.
        Monitoring agents usually ignore message content.
        """
        if context is None:
            context = {}

        # Start background monitoring only once
        if not context.get("monitoring_started"):
            context["monitoring_started"] = True
            self.start()

        return "Monitoring agent running"


    # ---------------- START ----------------
    def start(self):
        threading.Thread(target=self.poll_logs, daemon=True).start()
        threading.Thread(target=self.poll_metrics, daemon=True).start()
        while True:
            time.sleep(1)