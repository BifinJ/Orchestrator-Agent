import json
from .utils import parse_timestamp


def normalize_metric(raw):
    metric_name = raw["metric"]
    value = raw["value"]

    normalized = {
        "timestamp": raw["timestamp"],
        "service": "api",  
        "CPU_Usage": None,
        "Memory_Usage": None,
        "Network_In": None,
        "Network_Out": None
    }

    if metric_name == "CPUUtilization":
        normalized["CPU_Usage"] = value
    elif metric_name == "NetworkPacketsIn":
        normalized["Network_In"] = value
    elif metric_name == "NetworkPacketsOut":
        normalized["Network_Out"] = value

    return normalized


def load_metrics(file_path):
    metrics = []
    with open(file_path) as f:
        for line in f:
            raw = json.loads(line)
            raw["timestamp"] = parse_timestamp(raw["timestamp"])
            metrics.append(normalize_metric(raw))
    return metrics


def load_logs(file_path):
    logs = []
    with open(file_path) as f:
        for line in f:
            parts = line.split(" ")
            timestamp = parse_timestamp(parts[0])
            level = parts[3].strip("[]")  # [INFO], [ERROR]
            message = " ".join(parts[4:])
            logs.append({
                "timestamp": timestamp,
                "level": level,
                "message": message.strip()
            })
    return logs

