# agents/remediation_agent/llm_fallback.py
# Algorithm lines 3-4: A ← GenerateActions_LLM(C, constraints)

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except Exception:
    genai = None
    GENAI_AVAILABLE = False

SYSTEM = """
You are an automated DevOps remediation engine.

Return a COMPLETE and VALID JSON array.
Do NOT use markdown.
Do NOT use code fences.
Do NOT include explanations or comments.

Rules:
- Output MUST start with '[' and end with ']'
- Maximum 3 actions
- Each action MUST have exactly these keys:
  - action (string)
  - reversible (boolean)
  - cost (number between 0 and 1)
  - blast_radius (number between 0 and 1)

If you cannot comply, return an empty JSON array: []
"""

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Configure Gemini client
if GENAI_AVAILABLE and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Dynamic discovery to prevent 404 errors
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = next((m for m in models if "gemini-1.5-flash" in m), models[0])
        model = genai.GenerativeModel(target,system_instruction=SYSTEM)
    except Exception as e:
        print(f"[DEBUG] LLM Setup Error: {e}")

def generate_actions_llm(root_cause: str) -> list[dict]:
    try:
        response = model.generate_content(
            f"Root cause: {root_cause}",
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 256
            }
        )
        print("[DEBUG] Raw Gemini response:", response)
        text = response.text.strip()
        actions = json.loads(text)

        print(f"[LLM FALLBACK] Generated {len(actions)} actions for '{root_cause}'")
        return actions

    except Exception as e:
        print(f"[LLM FALLBACK] Failed: {e}")
        return []

if __name__ == "__main__":
    print("[LLM FALLBACK] Standalone test mode (hardcoded input)")

    # 🔒 Hard-coded root cause for demo/testing
    root_cause = "API service experiencing high latency due to thread pool exhaustion"

    print(f"[INPUT] Root cause: {root_cause}")

    actions = generate_actions_llm(root_cause)

    if not actions:
        print("[RESULT] No actions generated")
    else:
        print("[RESULT] Generated actions:")
        print(json.dumps(actions, indent=2))
