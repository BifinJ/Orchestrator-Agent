# agents/remediation_agent/llm_fallback.py
# Algorithm lines 3-4: A ← GenerateActions_LLM(C, constraints)

import os
import json
from dotenv import load_dotenv

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except Exception:
    genai = None
    GENAI_AVAILABLE = False


SYSTEM = """
Return EXACTLY three values in this format:

reversible,cost,blast_radius

Rules:
- reversible: true or false
- cost: number between 0 and 1
- blast_radius: number between 0 and 1
- NO spaces
- NO explanations
- NO markdown
- NO JSON

Example:
true,0.3,0.2
"""


load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

model = None

if GENAI_AVAILABLE and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)

        models = [
            m.name for m in genai.list_models()
            if "generateContent" in m.supported_generation_methods
        ]
        target = next((m for m in models if "gemini" in m), models[0])

        model = genai.GenerativeModel(
            target,
            system_instruction=SYSTEM
        )

    except Exception as e:
        print(f"[DEBUG] LLM Setup Error: {e}")


def _extract_text(response) -> str:
    """Safely extract text from Gemini response."""
    if hasattr(response, "candidates") and response.candidates:
        parts = response.candidates[0].content.parts
        return "".join(p.text for p in parts if hasattr(p, "text"))
    return response.text or ""


def generate_actions_llm(root_cause: str) -> list[dict]:
    """
    LLM fallback for remediation metadata.
    Returns a list with a single metadata dict.
    """

    # 🔒 Hardcoded SAFE fallback (deterministic)
    HARD_FALLBACK = {
        "reversible": True,
        "cost": 0.3,
        "blast_radius": 0.2
    }

    if not GENAI_AVAILABLE or not GEMINI_API_KEY:
        print("[LLM FALLBACK] Gemini unavailable — using hardcoded fallback")
        return [HARD_FALLBACK]

    try:
        response = model.generate_content(
            f"Root cause: {root_cause}",
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 128
            }
        )

        text = (response.text or "").strip()
        print("[DEBUG] Raw Gemini output:", text)

        data = json.loads(text)

        # 🚨 Validate strict contract
        if not isinstance(data, dict):
            raise ValueError("LLM output is not a JSON object")

        required_keys = {"reversible", "cost", "blast_radius"}
        if not required_keys.issubset(data.keys()):
            raise ValueError("LLM output missing required keys")

        # 🚧 Clamp values defensively
        data["cost"] = float(min(max(data["cost"], 0.0), 1.0))
        data["blast_radius"] = float(min(max(data["blast_radius"], 0.0), 1.0))
        data["reversible"] = bool(data["reversible"])

        return [data]

    except Exception as e:
        print(f"[LLM FALLBACK] Failed: {e}")
        print("[LLM FALLBACK] Using hardcoded fallback values")
        return [HARD_FALLBACK]

if __name__ == "__main__":
    print("[LLM FALLBACK] Standalone test mode (hardcoded input)")

    root_cause = "API service experiencing high latency due to thread pool exhaustion"
    print(f"[INPUT] Root cause: {root_cause}")

    actions = generate_actions_llm(root_cause)

    if not actions:
        print("[RESULT] No actions generated")
    else:
        print("[RESULT] Generated actions:")
        print(json.dumps(actions, indent=2))
