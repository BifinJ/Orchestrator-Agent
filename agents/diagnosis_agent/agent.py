import json
import math
from datetime import datetime, timedelta
from collections import deque



TIME_WINDOW_MINUTES = 5

WEIGHTS = {
    "metric": 0.4,
    "log": 0.2,
    "dependency": 0.3,
    "temporal": 0.1
}


DEPENDENCY_GRAPH = {
    "api": ["auth", "db"],
    "auth": ["db"],
    "db": ["cache", "storage"],
    "cache": ["storage"],
    "storage": []
}



def parse_timestamp(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

def temporal_decay(event_time, anomaly_time):
    delta = abs((anomaly_time - event_time).total_seconds())
    return math.exp(-delta / (TIME_WINDOW_MINUTES * 60))


def dependency_distance(source, target):
    """Shortest path distance using BFS"""
    if source == target:
        return 0

    visited = set()
    queue = deque([(source, 0)])

    while queue:
        node, dist = queue.popleft()
        if node == target:
            return dist
        for dep in DEPENDENCY_GRAPH.get(node, []):
            if dep not in visited:
                visited.add(dep)
                queue.append((dep, dist + 1))

    return float("inf")

def dependency_score(source, target):
    dist = dependency_distance(source, target)
    if dist == float("inf"):
        return 0.0
    return max(0.0, 1.0 - (0.3 * dist))



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


class DiagnosticAgent:
    def __init__(self, metrics, logs):
        self.metrics = metrics
        self.logs = logs

    def analyze(self, anomaly_event):
        """
        anomaly_event example:
        {
            "service": "api",
            "timestamp": "2025-12-07T17:21:33Z",
            "type": "HIGH_CPU"
        }
        """

        anomaly_time = parse_timestamp(anomaly_event["timestamp"])
        affected_service = anomaly_event["service"]

        window_start = anomaly_time - timedelta(minutes=TIME_WINDOW_MINUTES)
        window_end = anomaly_time + timedelta(minutes=TIME_WINDOW_MINUTES)

        # ---- Filter relevant metrics ----
        relevant_metrics = [
            m for m in self.metrics
            if window_start <= m["timestamp"] <= window_end
        ]

        # ---- Filter relevant error logs ----
        relevant_logs = [
            l for l in self.logs
            if l["level"] == "ERROR"
            and window_start <= l["timestamp"] <= window_end
        ]

        # ---- Candidate root causes (upstream traversal) ----
        candidates = self.get_all_upstream(affected_service)
        candidates.insert(0, affected_service)

        diagnosis = []

        for service in candidates:
            dep_score = dependency_score(affected_service, service)
            log_score = 1.0 if relevant_logs else 0.0
            metric_score = 1.0 if relevant_metrics else 0.0
            temporal_score = temporal_decay(anomaly_time, anomaly_time)

            confidence = (
                WEIGHTS["metric"] * metric_score +
                WEIGHTS["log"] * log_score +
                WEIGHTS["dependency"] * dep_score +
                WEIGHTS["temporal"] * temporal_score
            )

            diagnosis.append({
                "root_cause": service.upper(),
                "confidence": round(confidence, 2),
                "evidence": {
                    "dependency_distance": dependency_distance(affected_service, service),
                    "metrics_seen": len(relevant_metrics),
                    "error_logs_seen": len(relevant_logs)
                }
            })

        return sorted(diagnosis, key=lambda x: x["confidence"], reverse=True)

    # --------------------------------------------------

    def get_all_upstream(self, service, visited=None):
        if visited is None:
            visited = set()

        causes = []
        for src, deps in DEPENDENCY_GRAPH.items():
            if service in deps and src not in visited:
                visited.add(src)
                causes.append(src)
                causes.extend(self.get_all_upstream(src, visited))
        return causes



if __name__ == "__main__":
    metrics = load_metrics("metric_history.log")
    logs = load_logs("monitor_logs.log")

    # ---- Monitoring Agent output (simulated) ----
    anomaly_event = {
        "service": "api",
        "timestamp": "2025-12-07T17:21:33.204907Z",
        "type": "HIGH_CPU"
    }

    agent = DiagnosticAgent(metrics, logs)
    results = agent.analyze(anomaly_event)

    print("\n=== DIAGNOSTIC REPORT (DEPENDENCY-AWARE) ===\n")
    for i, r in enumerate(results, 1):
        print(f"{i}. Root Cause: {r['root_cause']}")
        print(f"   Confidence: {r['confidence']}")
        print(f"   Evidence: {r['evidence']}\n")
