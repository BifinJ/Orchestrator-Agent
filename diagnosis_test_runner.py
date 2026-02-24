import time
import random
import json
from datetime import datetime, timezone
from collections import defaultdict

from agents.diagnosis_agent.diagnostic_agent import DiagnosticAgent

# -----------------------------------------
# CONFIG
# -----------------------------------------

TEST_SERVICES = ["database", "auth", "api", "storage", "network", "cache"]
NUM_TESTS_PER_SERVICE = 30

# -----------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------

def now_iso():
    return datetime.now(timezone.utc).isoformat()


def create_direct_failure(service):
    """
    Direct service failure.
    Expected root cause = same service.
    """
    return {
        "alert": {
            "service": service,
            "type": "error",
            "timestamp": now_iso(),
            "message": f"{service} failure"
        },
        "expected": service
    }


def create_dependency_failure(service):
    """
    Simulate upstream failure.
    Example:
        database fails → api alert
        network fails → database alert
    """
    dependency_map = {
        "database": "api",
        "network": "database",
        "storage": "database",
        "auth": "api",
        "cache": "api"
    }

    if service not in dependency_map:
        return None

    affected = dependency_map[service]

    return {
        "alert": {
            "service": affected,
            "type": "error",
            "timestamp": now_iso(),
            "message": f"{affected} degraded due to {service}"
        },
        "expected": service
    }


def create_metric_failure(service):
    """
    Simulate metric anomaly.
    """
    return {
        "alert": {
            "service": service,
            "type": "metric_anomaly",
            "metric": "CPUUtilization",
            "zscore": random.uniform(3.0, 6.0),
            "timestamp": now_iso()
        },
        "expected": service
    }


# -----------------------------------------
# EVALUATION CORE
# -----------------------------------------

def evaluate():
    agent = DiagnosticAgent(metrics=[], logs=[])

    results = []
    confusion = defaultdict(lambda: defaultdict(int))
    per_class_correct = defaultdict(int)
    per_class_total = defaultdict(int)

    latencies = []
    confidences = []

    print("🔬 Running Controlled Diagnosis Evaluation\n")

    for service in TEST_SERVICES:

        for _ in range(NUM_TESTS_PER_SERVICE):

            scenario_type = random.choice(["direct", "dependency", "metric"])

            if scenario_type == "direct":
                scenario = create_direct_failure(service)

            elif scenario_type == "dependency":
                scenario = create_dependency_failure(service)
                if scenario is None:
                    scenario = create_direct_failure(service)

            else:
                scenario = create_metric_failure(service)

            alert = scenario["alert"]
            expected = scenario["expected"]

            start = time.time()
            diagnoses = agent.handle_anomaly(alert)
            latency = time.time() - start

            latencies.append(latency)

            if not diagnoses:
                predicted = "none"
                confidence = 0
            else:
                predicted = diagnoses[0]["root_cause"].lower()
                confidence = diagnoses[0]["confidence"]

            confidences.append(confidence)

            correct = (predicted == expected)

            per_class_total[expected] += 1
            if correct:
                per_class_correct[expected] += 1

            confusion[expected][predicted] += 1

            results.append({
                "expected": expected,
                "predicted": predicted,
                "confidence": confidence,
                "latency": latency,
                "correct": correct
            })

    # -----------------------------------------
    # METRICS
    # -----------------------------------------

    total = len(results)
    correct_total = sum(1 for r in results if r["correct"])
    accuracy = correct_total / total

    avg_latency = sum(latencies) / total
    avg_confidence = sum(confidences) / total

    print("===================================================")
    print("DIAGNOSIS EVALUATION SUMMARY")
    print("===================================================")
    print(f"Total Tests: {total}")
    print(f"Overall Accuracy: {round(accuracy*100,2)} %")
    print(f"Average Latency (sec): {round(avg_latency,6)}")
    print(f"Average Confidence: {round(avg_confidence,3)}")
    print("===================================================\n")

    print("Per-Class Accuracy:")
    for svc in TEST_SERVICES:
        if per_class_total[svc] > 0:
            acc = per_class_correct[svc] / per_class_total[svc]
            print(f"{svc}: {round(acc*100,2)} %")

    # Save results
    with open("diagnosis_evaluation_results.json", "w") as f:
        json.dump({
            "total_tests": total,
            "accuracy": accuracy,
            "average_latency_sec": avg_latency,
            "average_confidence": avg_confidence,
            "per_class_accuracy": {
                svc: per_class_correct[svc] / per_class_total[svc]
                for svc in TEST_SERVICES
            },
            "confusion_matrix": confusion
        }, f, indent=4)

    print("\nResults saved to diagnosis_evaluation_results.json")


if __name__ == "__main__":
    evaluate()
