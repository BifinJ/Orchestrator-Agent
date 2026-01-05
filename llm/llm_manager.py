# import os
# import json
# import re
# import google.generativeai as genai
# from dotenv import load_dotenv
# from data.logger import logger

# load_dotenv()

# class LLMManager:
#     def __init__(self, provider="gemini-2.5-flash-lite"):
#         self.provider = provider
#         api_key = os.getenv("GEMINI_API_KEY")
#         if not api_key:
#             raise ValueError("Missing GEMINI_API_KEY in .env")
#         genai.configure(api_key=api_key)
#         self.model = genai.GenerativeModel(provider)

#         # 🧠 Simple in-memory context
#         self.context_memory = []

#     def _update_context(self, role: str, content: str):
#         """Store limited chat history (acts as memory)."""
#         self.context_memory.append({"role": role, "content": content})
#         # Keep last 5 interactions only (you can tune this)
#         if len(self.context_memory) > 10:
#             self.context_memory = self.context_memory[-10:]

#     def _build_context_prompt(self, user_message: str) -> str:
#         """Combine previous interactions into a contextualized prompt."""
#         memory_text = "\n".join(
#             [f"{m['role'].capitalize()}: {m['content']}" for m in self.context_memory]
#         )
#         return f"Conversation so far:\n{memory_text}\n\nCurrent User: {user_message}"

#     async def classify_agents(self, message: str, registry_summary: str) -> list[str]:
#         """
#         Uses Gemini API to classify a user prompt and return multiple agent names.
#         Includes short-term conversational memory.
#         """
#         # 🧠 Build prompt with memory
#         contextual_message = self._build_context_prompt(message)
#         print("memory",contextual_message)
#         prompt = (
#             "You are an orchestrator assistant that selects relevant agents.\n"
#             "Given the conversation context, user request, and list of available agents with capabilities, "
#             "return the names of the agents that should handle this task. "
#             "If multiple agents are needed return all. Return ONLY a JSON array of agent names.\n\n"
#             f"Agents:\n{registry_summary}\n\n"
#             f"User request: {contextual_message}\n"
#             "Return format example: [\"monitoring_agent\", \"cost_agent\"]"
#         )

#         try:
#             response = self.model.generate_content(prompt)
#             raw = response.candidates[0].content.parts[0].text.strip()
#             print("Raw output:", raw)
#             logger.debug(f"Gemini raw output: {raw}")
#             cleaned = re.sub(r"^```(json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE).strip()

#             try:
#                 parsed = json.loads(cleaned)
#                 if isinstance(parsed, list):
#                     # 🧠 Save this turn to memory
#                     self._update_context("user", message)
#                     self._update_context("assistant", f"Agents selected: {parsed}")
#                     print("Parsed:", parsed)
#                     return parsed
#                 else:
#                     logger.warning("Gemini returned non-list structure.")
#                     return []
#             except json.JSONDecodeError as e:
#                 logger.error(f"JSON parsing failed: {e}")
#                 return []

#             start, end = raw.find("["), raw.find("]") + 1
#             if start != -1 and end != -1:
#                 arr = json.loads(raw[start:end])
#                 return arr if isinstance(arr, list) else []

#         except Exception as e:
#             logger.error(f"Gemini classification error: {e}")

#         return []
import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv
from data.logger import logger

load_dotenv()

class LLMManager:
    def __init__(self, provider="gemini-2.5-flash-lite"):
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

    def _build_context_prompt(self) -> str:
        """Combine previous interactions into a readable format."""
        if not self.context_memory:
            return "No previous conversation."
        
        memory_text = "\n".join(
            [f"{m['role'].capitalize()}: {m['content']}" for m in self.context_memory]
        )
        return f"Conversation History:\n{memory_text}"

    async def classify_agents(self, message: str, registry_summary: str) -> list[str]:
        """
        Uses Gemini API to classify a user prompt and return multiple agent names.
        Includes short-term conversational memory.
        """
        # 🧠 Build prompt with memory
        contextual_prompt = self._build_context_prompt()
        
        prompt = (
            "You are an orchestrator assistant that selects relevant agents.\n"
            "Given the conversation context, user request, and list of available agents with capabilities, "
            "return the names of the agents that should handle this task. "
            "If multiple agents are needed, return all. Return ONLY a JSON array of agent names.\n\n"
            f"{contextual_prompt}\n\n"
            f"Available Agents:\n{registry_summary}\n\n"
            f"Current User Request: {message}\n\n"
            "Return format example: [\"monitoring_agent\", \"cost_agent\"]"
        )

        try:
            response = self.model.generate_content(prompt)
            raw = response.candidates[0].content.parts[0].text.strip()
            logger.debug(f"Agent classification raw output: {raw}")
            
            cleaned = re.sub(r"^```(json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE).strip()

            try:
                parsed = json.loads(cleaned)
                if isinstance(parsed, list):
                    logger.info(f"Selected agents: {parsed}")
                    return parsed
                else:
                    logger.warning("Gemini returned non-list structure.")
                    return []
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed: {e}")
                return []

        except Exception as e:
            logger.error(f"Gemini classification error: {e}")
            return []

    async def generate_agent_queries(
        self, 
        user_message: str, 
        selected_agents: list[str],
        registry_summary: str
    ) -> dict[str, str]:
        """
        Generate agent-specific queries for each selected agent.
        
        Args:
            user_message: Original user query
            selected_agents: List of agent names that were selected
            registry_summary: Full agent registry with descriptions
        
        Returns:
            Dict mapping agent_name -> tailored_query
        """
        if not selected_agents:
            return {}
        
        # Build context for the prompt
        contextual_prompt = self._build_context_prompt()
        
        # Extract only selected agent descriptions
        selected_agent_info = "\n".join([
            line for line in registry_summary.split("\n")
            if any(agent in line for agent in selected_agents)
        ])
        
        prompt = f"""You are a query decomposition assistant. Your job is to create agent-specific queries.

{contextual_prompt}

Current User Query: "{user_message}"

Selected Agents and Their Capabilities:
{selected_agent_info}

Instructions:
1. First, resolve any pronouns (it, that, this, they) or incomplete references using the conversation history
2. For EACH selected agent, create a tailored query that:
   - Is specific to that agent's expertise and capabilities
   - Is complete and standalone (includes necessary context from conversation history)
   - Clearly asks what information that agent should provide
   - Focuses on the agent's domain (e.g., cost_agent gets pricing questions, monitoring_agent gets metric questions)

3. Return ONLY a JSON object mapping agent names to their specific queries

Example format:
{{
  "static_agent": "What is EC2 and what are its key features?",
  "cost_agent": "What is the pricing structure for EC2 instances?",
  "monitoring_agent": "What metrics should be monitored for EC2 instances?"
}}

Important:
- Each query should be unique and focused on that agent's specialty
- Resolve all pronouns using conversation history
- Make queries standalone (don't rely on previous messages)
- Keep queries concise but complete

Return the JSON object now:"""

        try:
            response = self.model.generate_content(prompt)
            raw = response.text.strip()
            logger.debug(f"Agent query generation raw output: {raw}")
            
            # Clean markdown code blocks
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE).strip()
            
            agent_queries = json.loads(cleaned)
            
            # Validate that all selected agents have queries
            for agent in selected_agents:
                if agent not in agent_queries:
                    logger.warning(f"Missing query for {agent}, using original message")
                    agent_queries[agent] = user_message
            
            logger.info(f"Generated agent-specific queries: {agent_queries}")
            
            # 🧠 Update memory with this interaction
            self._update_context("user", user_message)
            self._update_context("system", f"Agents queried: {list(agent_queries.keys())}")
            
            return agent_queries
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse agent queries JSON: {e}")
            # Fallback: all agents get the same query
            return {agent: user_message for agent in selected_agents}
        
        except Exception as e:
            logger.error(f"Agent query generation error: {e}")
            # Fallback: all agents get the same query
            return {agent: user_message for agent in selected_agents}

    def update_memory_with_response(self, fused_response: str):
        """
        Update memory with the final fused response.
        Call this after getting the final answer.
        """
        self._update_context("assistant", fused_response)
        logger.debug("Memory updated with fused response")

    def clear_memory(self):
        """Clear conversation memory."""
        self.context_memory = []
        logger.info("LLM Manager memory cleared")