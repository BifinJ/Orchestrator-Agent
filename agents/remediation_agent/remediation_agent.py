# agents/remediation_agent/remediation_agent.py

from agents.remediation_agent.decision_engine import decide_action
from agents.remediation_agent.executor import execute_action
from agents.learning.action_store import record_action
from agents.learning.incident_store import record_incident
from datetime import datetime


def remediation_agent(payload: dict):
    """
    Payload:
    {
        "alert": {...},
        "diagnosis": [...]
    }
    """

    alert = payload.get("alert")
    diagnosis = payload.get("diagnosis", [])

    if not diagnosis:
        print("[REMEDIATION] No diagnosis provided.")
        return

    # Take top-ranked diagnosis
    top = diagnosis[0]

    decision = decide_action(top)

    if not decision["approved"]:
        print(f"[REMEDIATION] Action requires approval: {decision['action']}")
        return

    print(f"[REMEDIATION] Executing action: {decision['action']}")

    result = execute_action(decision["action"])

    # ---- Learning feedback ----
    record_action(
        action=decision["action"],
        success=result["success"],
        recovery_time=result["recovery_time"]
    )

    record_incident(
        anomaly=alert,
        diagnosis=diagnosis,
        resolved_root_cause=top["root_cause"],
        remediation={
            "action": decision["action"],
            "success": result["success"],
            "recovery_time_sec": result["recovery_time"],
            "timestamp": datetime.utcnow().isoformat()
        }
    )
