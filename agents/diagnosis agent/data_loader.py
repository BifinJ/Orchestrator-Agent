import json
from utils import parse_timestamp

def load_metrics(file_path):
    metrics = []
    with open(file_path, "r") as f:
        for line in f:
            m = json.loads(line)
            m["timestamp"] = parse_timestamp(m["timestamp"])
            metrics.append(m)
    return metrics

def load_logs(file_path):
    logs = []
    with open(file_path, "r") as f:
        for line in f:
            parts = line.split(" ")
            logs.append({
                "timestamp": parse_timestamp(parts[0]),
                "level": parts[-2].strip("[]"),
                "message": " ".join(parts[-1:])
            })
    return logs
