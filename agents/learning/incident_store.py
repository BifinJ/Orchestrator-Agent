import json
from pathlib import Path

INCIDENT_LOG = Path("learning/incidents.jsonl")

def record_incident(anomaly, diagnosis, resolved_root_cause, remediation):
    record = {
        "anomaly": anomaly,
        "diagnosis": diagnosis,
        "resolved_root_cause": resolved_root_cause,
        "remediation": remediation
    }

    with open(INCIDENT_LOG, "a") as f:
        f.write(json.dumps(record) + "\n")
