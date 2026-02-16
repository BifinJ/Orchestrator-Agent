# agents/remediation_agent/decision_engine.py

from agents.remediation_agent.book import BOOK
from agents.remediation_agent.llm_fallback import generate_actions_llm
from agents.remediation_agent.policy import W1, W2, W3, W4, SAFETY_THRESHOLD


def decide_action(diagnosis: dict) -> dict:
    confidence = diagnosis.get("confidence", 0.0)   # γ
    root_cause = diagnosis.get("root_cause", "")

    # ── Line 1: A ← RetrievePlaybook(C) ─────────────────────────────────────
    actions = BOOK.get(root_cause, [])

    # ── Lines 2–4: if A = ∅ → LLM fallback ──────────────────────────────────
    if not actions:
        print(f"[DECISION] No playbook entry for '{root_cause}' — using LLM")
        actions = generate_actions_llm(root_cause)

    if not actions:
        return {
            "approved":      False,
            "action":        None,
            "risk":          None,
            "confidence":    confidence,
            "score":         None,
            "justification": f"No actions found for root cause '{root_cause}'"
        }

    # ── Lines 5–9: score each action ─────────────────────────────────────────
    # κ(a) = EstimateCost, ρ(a) = IsReversible, β(a) = ComputeBlastRadius
    # S(a) = w1*γ + w2*ρ(a) − w3*κ(a) − w4*β(a)
    scored = []
    for a in actions:
        kappa = a.get("cost",         0.5)                      # κ(a)
        rho   = 1.0 if a.get("reversible", False) else 0.0     # ρ(a)
        beta  = a.get("blast_radius", 0.5)                      # β(a)
        score = W1 * confidence + W2 * rho - W3 * kappa - W4 * beta   # S(a)

        scored.append({**a, "score": score, "rho": rho,
                           "kappa": kappa, "beta": beta})

        print(f"[DECISION] {a['action']}: S={score:.3f} "
              f"(γ={confidence:.2f} ρ={rho} κ={kappa} β={beta})")

    # ── Line 10: a* = argmax S(a) ────────────────────────────────────────────
    best = max(scored, key=lambda a: a["score"])
    print(f"[DECISION] a* = {best['action']}  S={best['score']:.3f}  "
          f"θ_safe={SAFETY_THRESHOLD}")

    # ── Line 11: if S(a*) > θ_safe → auto-execute, else escalate ────────────
    approved = best["score"] > SAFETY_THRESHOLD

    return {
        "approved":      approved,
        "action":        best["action"],
        "risk":          best.get("risk", "unknown"),
        "confidence":    confidence,
        "score":         best["score"],
        "justification": (
            f"a*={best['action']} S={best['score']:.3f} | "
            f"γ={confidence:.2f} ρ={best['rho']} "
            f"κ={best['kappa']} β={best['beta']} θ={SAFETY_THRESHOLD}"
        )
    }