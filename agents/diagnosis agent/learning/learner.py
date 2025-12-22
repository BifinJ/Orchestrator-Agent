import json
from pathlib import Path
from learning.model import extract_features
from learning.action_store import record_action

INCIDENT_LOG = Path("learning/incidents.jsonl")

def train():
    if not INCIDENT_LOG.exists():
        print("[Learner] No incidents to learn from.")
        return None

    correct_distances = []
    correct_logs = []
    correct_metrics = []

    processed_actions = 0

    with open(INCIDENT_LOG) as f:
        for line in f:
            if not line.strip():
                continue

            record = json.loads(line)


            actual = record.get("resolved_root_cause")
            diagnosis = record.get("diagnosis", [])

            for d in diagnosis:
                if d["root_cause"] == actual.upper():
                    features = extract_features(d)
                    correct_distances.append(features[0])
                    correct_metrics.append(features[1])
                    correct_logs.append(features[2])


            remediation = record.get("remediation")
            if remediation:
                record_action(
                    action=remediation["action"],
                    success=remediation["success"],
                    recovery_time=remediation["recovery_time_sec"]
                )
                processed_actions += 1

    if not correct_distances:
        print("[Learner] No correct diagnostic matches found.")
        return None

    learned_weights = {
        "dependency": round(1 / (sum(correct_distances) / len(correct_distances) + 1), 3),
        "metric": round(sum(correct_metrics) / len(correct_metrics), 3),
        "log": round(sum(correct_logs) / len(correct_logs), 3)
    }

    print(f"[Learner] Learned diagnostic weights: {learned_weights}")
    print(f"[Learner] Processed {processed_actions} remediation outcomes.")

    return learned_weights
