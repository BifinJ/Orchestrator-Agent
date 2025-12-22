#!/usr/bin/env python3
"""
metrics_generator.py

- Generates realistic random metrics every 60 seconds
- Overwrites latest snapshot to metrics/metrics.json
- Appends history lines (JSON per line) to metrics/metrics_history.log
"""
import os
import time
import json
import random
from datetime import datetime, timezone

METRICS_DIR = "metrics"
METRICS_FILE = os.path.join(METRICS_DIR, "metrics.json")
METRICS_HISTORY = os.path.join(METRICS_DIR, "metrics_history.log")

os.makedirs(METRICS_DIR, exist_ok=True)

def generate_metrics():
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    metrics = {
        "timestamp": now,
        "CPU_Usage": random.randint(10, 95),
        "Memory_Usage": random.randint(15, 95),
        "DB_Connections": random.randint(0, 30),
        "Request_Rate": random.randint(0, 500)
    }
    return metrics

def save_metrics(metrics):
    # latest snapshot
    with open(METRICS_FILE, "w") as f:
        json.dump(metrics, f, indent=2)

    # append history (one JSON object per line)
    with open(METRICS_HISTORY, "a") as f:
        f.write(json.dumps(metrics) + "\n")

def start(interval_seconds=60):
    print(f"[metrics_generator] started (interval={interval_seconds}s). Writing to {METRICS_FILE} and {METRICS_HISTORY}")
    while True:
        m = generate_metrics()
        save_metrics(m)
        print(f"[metrics_generator] generated: {m}")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    start(60)
