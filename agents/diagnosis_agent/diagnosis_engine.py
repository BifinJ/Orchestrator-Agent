from datetime import timedelta
from .config import TIME_WINDOW_MINUTES, WEIGHTS
from .dependency_graph import DEPENDENCY_GRAPH
from .utils import dependency_score, dependency_distance, temporal_decay
from .learning.action_mapping import ROOT_CAUSE_ACTIONS, ACTION_RISK
from .learning.action_store import get_action_stats


class DiagnosisEngine:
    def __init__(self, metrics, logs):
        self.metrics = metrics
        self.logs = logs

    def update_weights(new_weights):
        from .config import WEIGHTS
        for k in new_weights:
            if k in WEIGHTS:
                WEIGHTS[k] = min(max(new_weights[k], 0.1), 0.6)

    def analyze(self, anomaly_time, affected_service):
        window_start = anomaly_time - timedelta(minutes=TIME_WINDOW_MINUTES)
        window_end = anomaly_time + timedelta(minutes=TIME_WINDOW_MINUTES)

        relevant_metrics = [
            m for m in self.metrics
            if isinstance(m, dict)
            and "timestamp" in m
            and window_start <= m["timestamp"] <= window_end
        ]

        relevant_logs = [
            l for l in self.logs
            if isinstance(l, dict)
            and l.get("level") == "ERROR"
            and "timestamp" in l
            and window_start <= l["timestamp"] <= window_end
        ]

        candidates = self.get_all_upstream(affected_service)
        candidates.insert(0, affected_service)

        diagnosis = []

        for service in candidates:
            confidence = (
                WEIGHTS["metric"] * (1.0 if relevant_metrics else 0.0) +
                WEIGHTS["log"] * (1.0 if relevant_logs else 0.0) +
                WEIGHTS["dependency"] * dependency_score(affected_service, service) +
                WEIGHTS["temporal"] * temporal_decay(anomaly_time, anomaly_time)
            )

            diagnosis.append({
                "root_cause": service.upper(),
                "confidence": round(confidence, 2),
                "evidence": {
                    "dependency_distance": dependency_distance(affected_service, service),
                    "metrics_seen": len(relevant_metrics),
                    "error_logs_seen": len(relevant_logs)
                },
                "recommended_actions": self.recommend_actions(service.upper())
            })

        return sorted(diagnosis, key=lambda x: x["confidence"], reverse=True)

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

    def recommend_actions(self, root_cause):
        actions = ROOT_CAUSE_ACTIONS.get(root_cause, [])
        recommendations = []

        for action in actions:
            stats = get_action_stats(action)
            recommendations.append({
                "action": action,
                "risk": ACTION_RISK.get(action, "unknown"),
                "success_rate": stats["success_rate"] if stats else None,
                "avg_recovery_time": stats["avg_recovery_time"] if stats else None
            })

        return recommendations
