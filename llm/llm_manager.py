import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()

class LLMManager:
    def __init__(self, provider="gemini-2.0-flash-lite"):
        self.provider = provider
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Missing GEMINI_API_KEY in .env")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(provider)

        # 🧠 Simple in-memory context
        self.context_memory = []

    def _update_context(self, role: str, content: str):
        """Store limited chat history (acts as memory)."""
        self.context_memory.append({"role": role, "content": content})
        # Keep last 5 interactions only (you can tune this)
        if len(self.context_memory) > 10:
            self.context_memory = self.context_memory[-10:]

    def _build_context_prompt(self, user_message: str) -> str:
        """Combine previous interactions into a contextualized prompt."""
        memory_text = "\n".join(
            [f"{m['role'].capitalize()}: {m['content']}" for m in self.context_memory]
        )
        return f"Conversation so far:\n{memory_text}\n\nCurrent User: {user_message}"

    async def classify_agents(self, message: str, registry_summary: str) -> list[str]:
        """
        Uses Gemini API to classify a user prompt and return multiple agent names.
        Includes short-term conversational memory.
        """
        # 🧠 Build prompt with memory
        contextual_message = self._build_context_prompt(message)
        print("memory",contextual_message)
        prompt = (
            "You are an orchestrator assistant that selects relevant agents.\n"
            "Given the conversation context, user request, and list of available agents with capabilities, "
            "return the names of the agents that should handle this task. "
            "If multiple agents are needed return all. Return ONLY a JSON array of agent names.\n\n"
            f"Agents:\n{registry_summary}\n\n"
            f"User request: {contextual_message}\n"
            "Return format example: [\"monitoring_agent\", \"cost_agent\"]"
        )

        try:
            response = self.model.generate_content(prompt)
            raw = response.candidates[0].content.parts[0].text.strip()
            print("Raw output:", raw)
            logger.debug(f"Gemini raw output: {raw}")
            cleaned = re.sub(r"^```(json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE).strip()

            try:
                parsed = json.loads(cleaned)
                if isinstance(parsed, list):
                    # 🧠 Save this turn to memory
                    self._update_context("user", message)
                    self._update_context("assistant", f"Agents selected: {parsed}")
                    print("Parsed:", parsed)
                    return parsed
                else:
                    logger.warning("Gemini returned non-list structure.")
                    return []
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed: {e}")
                return []

            start, end = raw.find("["), raw.find("]") + 1
            if start != -1 and end != -1:
                arr = json.loads(raw[start:end])
                return arr if isinstance(arr, list) else []

        except Exception as e:
            logger.error(f"Gemini classification error: {e}")

        return []
