
def extract_features(diagnosis_entry):
    evidence = diagnosis_entry["evidence"]

    return [
        evidence["dependency_distance"],
        evidence["metrics_seen"],
        evidence["error_logs_seen"]
    ]
