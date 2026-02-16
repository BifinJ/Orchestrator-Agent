# agents/remediation_agent/knowledge_base.py
# Algorithm: "Log execution to Knowledge Base"
# After logging, writes the outcome directly into the diagnosis learning base
# (incidents.jsonl + action_stats.json) so the learning loop closes
# without touching any file in the diagnosis or learning folders.

import json, os
from datetime import datetime
from pathlib import Path

KB_FILE           = "storage/knowledge_base.jsonl"
INCIDENT_LOG      = Path("learning/incidents.jsonl")    # read by learner.train()
ACTION_STATS_FILE = Path("storage/action_stats.json")   # mirrors action_store state


def log_execution(action: str, service: str,
                  result: dict, diagnosis: dict, decision: dict,
                  anomaly: dict = None, full_diagnosis_list: list = None):
    """
    1. Append to remediation KB  (unchanged behaviour).
    2. Append incident record to learning/incidents.jsonl
       so learner.train() picks it up and updates diagnostic weights.
    3. Update storage/action_stats.json in the same format action_store.py
       uses, so get_action_stats() returns live success rates next time
       the diagnosis engine calls recommend_actions().
    """
    os.makedirs("storage", exist_ok=True)

    # executor.py returns {'status': 'success'|'error', ...} not {'success': bool}
    success       = result.get("status") == "success"
    recovery_time = float(result.get("recovery_time_sec", 0))

    # ── 1. Remediation KB (unchanged) ────────────────────────────────────────
    entry = {
        "timestamp":     datetime.utcnow().isoformat() + "Z",
        "service":       service,
        "root_cause":    diagnosis.get("root_cause"),
        "confidence":    diagnosis.get("confidence"),
        "action":        action,
        "score":         decision.get("score"),
        "justification": decision.get("justification"),
        "success":       success,
    }
    with open(KB_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"[KB] Logged: {action} -> success={success}")

    # ── 2. Write incident into learning/incidents.jsonl ───────────────────────
    # Schema learner.train() expects: anomaly, diagnosis (list),
    # resolved_root_cause, remediation
    incident = {
        "anomaly":             anomaly or {"service": service},
        "diagnosis":           full_diagnosis_list or [diagnosis],
        "resolved_root_cause": diagnosis.get("root_cause", ""),
        "remediation": {
            "action":            action,
            "success":           success,
            "recovery_time_sec": recovery_time,
        },
    }

    os.makedirs(INCIDENT_LOG.parent, exist_ok=True)
    with open(INCIDENT_LOG, "a") as f:
        f.write(json.dumps(incident) + "\n")
    print(f"[KB->LEARNING] Incident appended to {INCIDENT_LOG} "
          f"(root_cause={diagnosis.get('root_cause')})")

    # ── 3. Update action_stats.json (same schema as action_store.py) ─────────
    # Written directly so action_store.get_action_stats() returns real numbers
    # next time diagnosis calls recommend_actions(), without touching action_store.py.
    stats = {}
    if ACTION_STATS_FILE.exists():
        try:
            with open(ACTION_STATS_FILE) as f:
                stats = json.load(f)
        except Exception:
            stats = {}

    if action not in stats:
        stats[action] = {"success": 0, "failure": 0, "total_recovery_time": 0}

    if success:
        stats[action]["success"] += 1
    else:
        stats[action]["failure"] += 1
    stats[action]["total_recovery_time"] += recovery_time

    with open(ACTION_STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"[KB->LEARNING] action_stats.json updated: {action} "
          f"success={success} recovery={recovery_time}s")