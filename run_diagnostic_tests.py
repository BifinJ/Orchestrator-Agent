import time
import random
import json
import math
from datetime import datetime, timezone
from collections import defaultdict
import numpy as np
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)

from agents.diagnosis_agent.diagnostic_agent import DiagnosticAgent


# -----------------------------------------
# CONFIG
# -----------------------------------------

TEST_SERVICES = ["database", "auth", "api", "storage", "network", "cache"]
NUM_TESTS_PER_SERVICE = 50   # increased for stronger evaluation
RANDOM_SEED = 42

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


# -----------------------------------------
# HELPERS
# -----------------------------------------

def now_iso():
    return datetime.now(timezone.utc).isoformat()


def create_direct_failure(service):
    return {
        "alert": {
            "service": service,
            "type": "error",
            "timestamp": now_iso(),
            "message": f"{service} failure"
        },
        "expected": service
    }


def create_metric_failure(service):
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
# CALIBRATION METRICS
# -----------------------------------------

def compute_brier_score(results):
    return np.mean([
        (r["confidence"] - int(r["correct"])) ** 2
        for r in results
    ])


def compute_ece(results, n_bins=10):
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    total = len(results)

    for i in range(n_bins):
        bin_lower = bins[i]
        bin_upper = bins[i + 1]

        bin_items = [
            r for r in results
            if bin_lower <= r["confidence"] < bin_upper
        ]

        if len(bin_items) == 0:
            continue

        avg_conf = np.mean([r["confidence"] for r in bin_items])
        avg_acc = np.mean([r["correct"] for r in bin_items])
        ece += (len(bin_items) / total) * abs(avg_conf - avg_acc)

    return ece


# -----------------------------------------
# MAIN EVALUATION
# -----------------------------------------

def evaluate():

    agent = DiagnosticAgent(metrics=[], logs=[])

    y_true = []
    y_pred = []

    results = []
    latencies = []

    print("🔬 Running Research-Grade Diagnosis Evaluation\n")

    for service in TEST_SERVICES:
        for _ in range(NUM_TESTS_PER_SERVICE):

            scenario = random.choice([
                create_direct_failure(service),
                create_metric_failure(service)
            ])

            alert = scenario["alert"]
            expected = scenario["expected"]

            start = time.time()
            diagnoses = agent.handle_anomaly(alert)
            latency = time.time() - start

            latencies.append(latency)

            if not diagnoses:
                predicted = "none"
                confidence = 0.0
            else:
                predicted = diagnoses[0]["root_cause"].lower()
                confidence = diagnoses[0]["confidence"]

            correct = (predicted == expected)

            y_true.append(expected)
            y_pred.append(predicted)

            results.append({
                "expected": expected,
                "predicted": predicted,
                "confidence": confidence,
                "latency": latency,
                "correct": correct
            })

    # -----------------------------------------
    # CORE METRICS
    # -----------------------------------------

    accuracy = np.mean([r["correct"] for r in results])

    precision_macro = precision_score(y_true, y_pred, average="macro", zero_division=0)
    recall_macro = recall_score(y_true, y_pred, average="macro", zero_division=0)
    f1_macro = f1_score(y_true, y_pred, average="macro", zero_division=0)

    precision_micro = precision_score(y_true, y_pred, average="micro", zero_division=0)
    recall_micro = recall_score(y_true, y_pred, average="micro", zero_division=0)
    f1_micro = f1_score(y_true, y_pred, average="micro", zero_division=0)

    cm = confusion_matrix(y_true, y_pred, labels=TEST_SERVICES)

    avg_latency = np.mean(latencies)
    std_latency = np.std(latencies)

    # 95% Confidence Interval for accuracy
    n = len(results)
    ci95 = 1.96 * math.sqrt((accuracy * (1 - accuracy)) / n)

    # Calibration
    brier = compute_brier_score(results)
    ece = compute_ece(results)

    # -----------------------------------------
    # PRINT SUMMARY
    # -----------------------------------------

    print("===================================================")
    print("DIAGNOSIS EVALUATION SUMMARY")
    print("===================================================")
    print(f"Total Tests: {n}")
    print(f"Accuracy: {accuracy:.4f} ± {ci95:.4f} (95% CI)")
    print(f"Macro F1: {f1_macro:.4f}")
    print(f"Micro F1: {f1_micro:.4f}")
    print(f"Precision (macro): {precision_macro:.4f}")
    print(f"Recall (macro): {recall_macro:.4f}")
    print(f"Avg Latency (sec): {avg_latency:.6f} ± {std_latency:.6f}")
    print(f"Brier Score: {brier:.4f}")
    print(f"ECE: {ece:.4f}")
    print("===================================================\n")

    print("Classification Report:\n")
    print(classification_report(y_true, y_pred, zero_division=0))

    # -----------------------------------------
    # SAVE SCIENTIFIC REPORT
    # -----------------------------------------

    report = {
        "total_tests": n,
        "accuracy": accuracy,
        "accuracy_ci95": ci95,
        "precision_macro": precision_macro,
        "recall_macro": recall_macro,
        "f1_macro": f1_macro,
        "precision_micro": precision_micro,
        "recall_micro": recall_micro,
        "f1_micro": f1_micro,
        "avg_latency_sec": float(avg_latency),
        "std_latency_sec": float(std_latency),
        "brier_score": brier,
        "expected_calibration_error": ece,
        "confusion_matrix": cm.tolist()
    }

    with open("diagnosis_research_evaluation.json", "w") as f:
        json.dump(report, f, indent=4)

    print("\nResearch evaluation saved to diagnosis_research_evaluation.json")


if __name__ == "__main__":
    evaluate()