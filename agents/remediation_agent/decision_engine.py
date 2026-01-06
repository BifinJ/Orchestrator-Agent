# agents/remediation_agent/decision_engine.py

from agents.remediation_agent.policy import (
    AUTO_APPROVE_RISK,
    CONFIDENCE_THRESHOLD
)


def decide_action(diagnosis: dict) -> dict:
    """
    Decide which action to take and whether it can be automated.
    """

    confidence = diagnosis["confidence"]
    actions = diagnosis.get("recommended_actions", [])

    if not actions:
        return {"approved": False}

    # Prefer lowest-risk action
    actions = sorted(actions, key=lambda a: a["risk"])
    selected = actions[0]

    approved = (
        confidence >= CONFIDENCE_THRESHOLD
        and selected["risk"] in AUTO_APPROVE_RISK
    )

    return {
        "approved": approved,
        "action": selected["action"],
        "risk": selected["risk"],
        "confidence": confidence
    }
