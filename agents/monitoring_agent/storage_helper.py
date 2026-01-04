import os
import json

LOG_ALERTS_PATH = "storage/log_alerts.json"
METRIC_ALERTS_PATH = "storage/metric_alerts.json"
LOCAL_LOG_COPY = "logs/monitor_logs.log"
METRICS_HISTORY_PATH = "metrics/metrics_history.log"

os.makedirs("storage", exist_ok=True)
os.makedirs("logs", exist_ok=True)
os.makedirs("metrics", exist_ok=True)

def append_json(path, alert):
    data = []
    if os.path.exists(path):
        with open(path, "r") as f:
            try:
                data = json.load(f)
            except:
                data = []
    data.append(alert)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def save_local_log(line):
    with open(LOCAL_LOG_COPY, "a") as f:
        f.write(line + "\n")

def append_metric(metric_record: dict):
    with open(METRICS_HISTORY_PATH, "a") as f:
        f.write(json.dumps(metric_record) + "\n")
