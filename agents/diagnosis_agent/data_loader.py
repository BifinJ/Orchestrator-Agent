import json
from datetime import datetime
from .utils import parse_timestamp


def load_logs(file_path):
    """
    Load and normalize application logs.

    Expected log format:
    2026-01-05T18:52:32+00:00 2026-01-05 18:52:32,187 [ERROR] Message
    """
    logs = []

    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split(" ")
            if len(parts) < 5:
                continue

            try:
                # Use the SECOND timestamp (the more precise one)
                timestamp_str = parts[1] + " " + parts[2]
                # Remove the comma from milliseconds
                timestamp_str = timestamp_str.replace(",", ".")
                timestamp = datetime.fromisoformat(timestamp_str)
            except Exception as e:
                print(f"[WARN] Failed to parse timestamp in log line: {line[:50]}... Error: {e}")
                continue

            level_token = parts[3]
            if level_token.startswith("[") and level_token.endswith("]"):
                level = level_token.strip("[]")
            else:
                continue

            message = " ".join(parts[4:])

            logs.append({
                "timestamp": timestamp,
                "level": level,
                "message": message
            })

    return logs


# --------------------------------------------------
# METRIC NORMALIZATION (UNCHANGED)
# --------------------------------------------------

def normalize_metric(raw):
    """
    Convert raw CloudWatch metric into a diagnostic signal.
    Only emits metrics that indicate a potential problem.
    """
    name = raw.get("metric")
    value = raw.get("value")
    timestamp = raw.get("timestamp")

    # ---- CPU PRESSURE ----
    if name == "CPUUtilization" and value >= 80:
        return {
            "timestamp": timestamp,
            "service": "api",
            "signal": "HIGH_CPU"
        }

    # ---- INSTANCE HEALTH ----
    if name == "StatusCheckFailed" and value == 1.0:
        return {
            "timestamp": timestamp,
            "service": "api",
            "signal": "INSTANCE_UNHEALTHY"
        }

    # ---- DISK PRESSURE ----
    if name == "EBSByteBalance%" and value <= 20:
        return {
            "timestamp": timestamp,
            "service": "db",
            "signal": "LOW_EBS_BALANCE"
        }

    # ---- NETWORK PRESSURE ----
    if name == "NetworkPacketsIn" and value >= 1000:
        return {
            "timestamp": timestamp,
            "service": "api",
            "signal": "HIGH_NETWORK_IN"
        }

    return None


def load_metrics(file_path):
    """
    Load and normalize CloudWatch metrics.
    Only metrics producing diagnostic signals are returned.
    """
    metrics = []

    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                raw = json.loads(line)
            except Exception:
                continue

            try:
                raw["timestamp"] = parse_timestamp(raw["timestamp"])
            except Exception:
                continue

            normalized = normalize_metric(raw)
            if normalized:
                metrics.append(normalized)

    return metrics