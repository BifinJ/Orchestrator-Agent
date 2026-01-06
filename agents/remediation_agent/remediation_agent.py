from datetime import datetime

from agents.remediation_agent.decision_engine import decide_action
from agents.remediation_agent.executor import execute_action
from agents.learning.action_store import record_action
from agents.learning.incident_store import record_incident


def remediation_agent(payload: dict):
    """
    Payload format:
    {
        "alert": {...},
        "diagnosis": [...]
    }
    """

    alert = payload.get("alert")
    diagnosis = payload.get("diagnosis", [])

    # --------------------------------------------------
    # Guard: no diagnosis
    # --------------------------------------------------
    if not diagnosis:
        print("[REMEDIATION] No diagnosis provided. Skipping remediation.")
        return

    # --------------------------------------------------
    # Take highest confidence diagnosis
    # --------------------------------------------------
    top = diagnosis[0]
    root_cause = top.get("root_cause", "UNKNOWN")

    decision = decide_action(top)

    # --------------------------------------------------
    # Guard: decision not approved
    # --------------------------------------------------
    if not decision.get("approved"):
        reason = decision.get("reason", "Not approved for automation")
        print(
            f"[REMEDIATION] Skipping remediation for {root_cause}: {reason}"
        )
        return

    action = decision.get("action")

    # --------------------------------------------------
    # Guard: no executable action
    # --------------------------------------------------
    if not action:
        print(
            f"[REMEDIATION] No executable action for root cause {root_cause}"
        )
        return

    # --------------------------------------------------
    # Execute remediation
    # --------------------------------------------------
    print(f"[REMEDIATION] Executing action: {action}")

    result = execute_action(action)

    success = result.get("success", False)
    recovery_time = result.get("recovery_time", None)

    print(
        f"[REMEDIATION] Result: "
        f"{'SUCCESS' if success else 'FAILURE'} "
        f"(recovery_time={recovery_time}s)"
    )

    # --------------------------------------------------
    # Learning feedback: action-level
    # --------------------------------------------------
    record_action(
        action=action,
        success=success,
        recovery_time=recovery_time
    )

    # --------------------------------------------------
    # Learning feedback: incident-level
    # --------------------------------------------------
    record_incident(
        anomaly=alert,
        diagnosis=diagnosis,
        resolved_root_cause=root_cause,
        remediation={
            "action": action,
            "success": success,
            "recovery_time_sec": recovery_time,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
