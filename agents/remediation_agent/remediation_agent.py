# agents/remediation_agent/remediation_agent.py

from datetime import datetime
import json, time, uuid, os

from agents.remediation_agent.decision_engine import decide_action
from agents.remediation_agent.executor        import execute_action
from agents.remediation_agent.knowledge_base  import log_execution
from agents.remediation_agent.monitor         import monitor_post_remediation

APPROVAL_FILE = "storage/approval.json"


def remediation_agent(payload: dict):
    print(f"[REMEDIATION] Triggered at {datetime.utcnow().isoformat()}Z")

    diagnosis_list = payload.get("diagnosis", [])
    if not diagnosis_list:
        return

    # Keep the full list so log_execution can write all candidates
    # into incidents.jsonl — learner.train() uses them to update weights.
    diagnosis = max(diagnosis_list, key=lambda d: d.get("confidence", 0))
    service   = diagnosis.get("root_cause") or payload.get("service", "unknown")
    anomaly   = payload.get("anomaly")  # original anomaly event from monitor

    decision = decide_action(diagnosis)
    action   = decision["action"]

    if action is None:
        _notify(f"No action: {decision['justification']}")
        return

    # ── AUTO EXECUTE (S(a*) > θ_safe) ────────────────────────────────────────
    if decision["approved"]:
        _notify(f"Auto remediation: {action} | {decision['justification']}")
        return _execute_and_resume(
            action, service, diagnosis, decision,
            anomaly=anomaly, full_diagnosis_list=diagnosis_list
        )

    # ── ESCALATE TO HUMAN (S(a*) ≤ θ_safe) ───────────────────────────────────
    incident_id = str(uuid.uuid4())
    _send_to_ui(incident_id, diagnosis, decision)

    if _wait_for_approval():
        _notify(f"Human approved: {action}")
        return _execute_and_resume(
            action, service, diagnosis, decision,
            anomaly=anomaly, full_diagnosis_list=diagnosis_list
        )

    _notify(f"Human rejected: {action}")


def _execute_and_resume(action: str, service: str,
                        diagnosis: dict, decision: dict,
                        anomaly: dict = None,
                        full_diagnosis_list: list = None) -> dict:
    """
    Execute -> Log to KB (which also writes back into the learning base) -> Monitor.
    anomaly and full_diagnosis_list are forwarded so the incident record
    written to incidents.jsonl is complete.
    """
    result = execute_action(action, service)
    print(f"[REMEDIATION] SUCCESS={result.get('success')}")

    log_execution(
        action, service, result, diagnosis, decision,
        anomaly=anomaly,
        full_diagnosis_list=full_diagnosis_list
    )
    monitor_post_remediation(service)

    return result


def _send_to_ui(incident_id: str, diagnosis: dict, decision: dict):
    os.makedirs("storage", exist_ok=True)
    with open(APPROVAL_FILE, "w") as f:
        json.dump({
            "incident_id":   incident_id,
            "service":       diagnosis.get("root_cause"),
            "action":        decision["action"],
            "risk":          decision["risk"],
            "confidence":    decision["confidence"],
            "score":         decision["score"],
            "justification": decision["justification"],
            "approved":      None
        }, f, indent=2)


def _wait_for_approval(timeout=120) -> bool:
    waited = 0
    while waited < timeout:
        with open(APPROVAL_FILE) as f:
            data = json.load(f)
        if data.get("approved") is True:
            _clear(); return True
        if data.get("approved") is False:
            _clear(); return False
        time.sleep(2)
        waited += 2
    _clear()
    return False


def _notify(msg: str):
    print(f"[NOTIFICATION] {msg}")


def _clear():
    with open(APPROVAL_FILE, "w") as f:
        json.dump({}, f)