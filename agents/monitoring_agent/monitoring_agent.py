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
from agents.monitoring_agent.service_detector import ServiceDetector


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
            name="MonitoringAgent"
        )
        self.seen_logs = set()
        self.status_events = []
        self.metric_history = {}
        self.last_log_ts = int(
            (datetime.now(timezone.utc) - timedelta(minutes=5)).timestamp() * 1000
        )

    # ==========================
    # LOG MONITORING
    # ==========================
    def poll_logs(self):
        print(f"[LOG] Monitoring {LOG_GROUP} dynamically...")

        while True:
            try:
                resp = logs_client.filter_log_events(
                    logGroupName=LOG_GROUP,
                    startTime=self.last_log_ts,
                    interleaved=True
                )

                for ev in resp.get("events", []):
                    self.last_log_ts = max(self.last_log_ts, ev["timestamp"] + 1)

                    msg = ev.get("message", "")
                    if not isinstance(msg, str):
                        continue

                    ts_iso = datetime.fromtimestamp(
                        ev["timestamp"] / 1000,
                        tz=timezone.utc
                    ).isoformat()

                    save_local_log(f"{ts_iso} {msg}")

                    # ---------------- SERVICE DETECTION (FROM LOG)
                    service = ServiceDetector.detect_service(message=msg)

                    # ---------------- KEYWORD ALERT
                    category = classify_log(msg)
                    if category:
                        alert = {
                            "type": category,
                            "service": service,
                            "timestamp": ts_iso,
                            "message": msg
                        }

                        append_json("storage/log_alerts.json", alert)
                        diagnosis = diagnostic_agent.handle_anomaly(alert)

                        if diagnosis:
                            remediation_agent({
                                "alert": alert,
                                "diagnosis": diagnosis,
                                "service": service
                            })

                    # ---------------- HTTP STATUS ALERT
                    status = detect_http_status(msg)
                    if status:
                        now = datetime.now(timezone.utc)
                        self.status_events.append((now, status))
                        self.status_events = [
                            e for e in self.status_events
                            if e[0] > now - timedelta(seconds=STATUS_WINDOW_SECONDS)
                        ]

                        count = sum(1 for _, s in self.status_events if s == status)

                        if count >= STATUS_ALERT_THRESHOLD:
                            alert = {
                                "type": "status_repeated",
                                "service": service,
                                "timestamp": ts_iso,
                                "status": status,
                                "count": count
                            }

                            append_json("storage/log_alerts.json", alert)
                            diagnosis = diagnostic_agent.handle_anomaly(alert)

                            if diagnosis:
                                remediation_agent({
                                    "alert": alert,
                                    "diagnosis": diagnosis,
                                    "service": service
                                })

            except Exception as e:
                print("[ERR] log polling:", e)

            time.sleep(5)

    # ==========================
    # METRIC MONITORING
    # ==========================
    def poll_metrics(self):
        print("[METRIC] Monitoring CloudWatch metrics dynamically...")

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

                    # --------- STORE METRIC
                    metric_record = {
                        "timestamp": ts_iso,
                        "namespace": namespace,
                        "metric": metric_name,
                        "value": value,
                        "dimensions": dimensions
                    }
                    append_metric(metric_record)

                    # --------- SERVICE DETECTION (FROM METRIC)
                    service = ServiceDetector.detect_service(
                        metric_name=metric_name,
                        namespace=namespace,
                        dimensions=dimensions
                    )

                    # --------- ZSCORE DETECTION
                    self.metric_history.setdefault(metric_name, []).append(value)
                    zs = rolling_zscore(self.metric_history[metric_name])

                    if zs[-1] is not None and abs(zs[-1]) > ZSCORE_THRESHOLD:
                        alert = {
                            "type": "metric_anomaly",
                            "service": service,
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
                                "diagnosis": diagnosis,
                                "service": service
                            })

            except Exception as e:
                print("[ERR] metric polling:", e)

            time.sleep(20)

    # ==========================
    # START THREADS
    # ==========================
    def start(self):
        threading.Thread(target=self.poll_logs, daemon=True).start()
        threading.Thread(target=self.poll_metrics, daemon=True).start()
        while True:
            time.sleep(1)
