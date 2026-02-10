from agents.remediation_agent.policy import (
    CONFIDENCE_THRESHOLD,
    AUTO_APPROVE_RISK
)


def decide_action(diagnosis: dict) -> dict:
    confidence = diagnosis.get("confidence", 0.0)
    actions = diagnosis.get("recommended_actions", [])

    if not actions:
        return {
            "approved": False,
            "reason": "No actions available",
            "action": None,
            "risk": None,
            "confidence": confidence
        }

    # pick lowest-risk action
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
