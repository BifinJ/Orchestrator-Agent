from datetime import datetime
import json, time, uuid, os

from agents.remediation_agent.decision_engine import decide_action
from agents.remediation_agent.executor import execute_action

APPROVAL_FILE = "storage/approval.json"


def remediation_agent(payload: dict):
    print(f"[REMEDIATION] Triggered at {datetime.utcnow().isoformat()}Z")

    diagnosis_list = payload.get("diagnosis", [])
    service = payload.get("service")
    if not diagnosis_list:
        return

    diagnosis = max(diagnosis_list, key=lambda d: d.get("confidence", 0))
    decision = decide_action(diagnosis)

    action = decision["action"]

    # ---- AUTO APPROVED ----
    if decision["approved"]:
        _notify(f"Auto remediation started: {action}")
        return _execute_and_resume(action)

    # ---- HUMAN APPROVAL ----
    incident_id = str(uuid.uuid4())
    _send_to_ui(incident_id, diagnosis, decision)

    approved = _wait_for_approval()

    if approved:
        _notify(f"Human approved remediation: {action}")
        return _execute_and_resume(action,service=service)

    _notify("Human rejected remediation")


def _send_to_ui(incident_id, diagnosis, decision):
    os.makedirs("storage", exist_ok=True)
    with open(APPROVAL_FILE, "w") as f:
        json.dump({
            "incident_id": incident_id,
            "service": diagnosis["root_cause"],
            "action": decision["action"],
            "risk": decision["risk"],
            "confidence": decision["confidence"],
            "approved": None
        }, f, indent=2)


def _wait_for_approval(timeout=120):
    waited = 0
    while waited < timeout:
        with open(APPROVAL_FILE) as f:
            data = json.load(f)

        if data.get("approved") is True:
            _clear()
            return True
        if data.get("approved") is False:
            _clear()
            return False

        time.sleep(2)
        waited += 2

    _clear()
    return False


def _execute_and_resume(action,service):
    result = execute_action(action,service)
    print(f"[REMEDIATION] SUCCESS={result['success']}")
    print("[REMEDIATION] Monitoring continues...")
    return result


def _notify(msg):
    print(f"[NOTIFICATION] {msg}")


def _clear():
    with open(APPROVAL_FILE, "w") as f:
        json.dump({}, f)
