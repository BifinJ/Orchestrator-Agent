# agents/remediation_agent/decision_engine.py

from agents.remediation_agent.policy import (
    AUTO_APPROVE_RISK,
    CONFIDENCE_THRESHOLD
)


def decide_action(diagnosis: dict) -> dict:
    confidence = diagnosis.get("confidence", 0.0)
    actions = diagnosis.get("recommended_actions", [])

    if not actions:
        return {
            "approved": False,
            "reason": "No remediation actions available"
        }

    actions = sorted(actions, key=lambda a: a["risk"])
    selected = actions[0]

    approved = (
        confidence >= CONFIDENCE_THRESHOLD
        and selected["risk"] in AUTO_APPROVE_RISK
    )

    return {
        "approved": approved,
        "action": selected.get("action"),
        "risk": selected.get("risk"),
        "confidence": confidence
    }
