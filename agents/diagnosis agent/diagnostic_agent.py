from utils import parse_timestamp
from diagnosis_engine import DiagnosisEngine

class DiagnosticAgent:
    def __init__(self, metrics, logs):
        self.engine = DiagnosisEngine(metrics, logs)

    def handle_anomaly(self, anomaly_event):
        anomaly_time = parse_timestamp(anomaly_event["timestamp"])
        affected_service = anomaly_event["service"]

        return self.engine.analyze(anomaly_time, affected_service)
