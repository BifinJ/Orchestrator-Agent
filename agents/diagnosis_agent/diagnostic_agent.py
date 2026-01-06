from .utils import parse_timestamp
from .diagnosis_engine import DiagnosisEngine
from .data_loader import load_metrics, load_logs

class DiagnosticAgent:
    def __init__(self, metrics, logs):
        print("[DIAG] Initializing Diagnostic Agent...")
        print(f"[DIAG] Loaded {len(metrics)} metrics and {len(logs)} logs for analysis.")
        self.engine = DiagnosisEngine(metrics, logs)

    def handle_anomaly(self, anomaly_event):
        print(f"[DIAG] Handling anomaly event: {anomaly_event}")
        anomaly_time = parse_timestamp(anomaly_event["timestamp"])
        affected_service = anomaly_event["service"]

        print(f"[DIAG] Analyzing anomaly at {anomaly_time} for service {affected_service}")

        fresh_metrics = load_metrics("metrics/metrics_history.log")
        fresh_logs = load_logs("logs/monitor_logs.log")

        # ---- inject into engine ----
        self.engine.metrics = fresh_metrics
        self.engine.logs = fresh_logs

        return self.engine.analyze(anomaly_time, affected_service)
