from llm.llm_manager import LLMManager
from typing import List, Dict
from utils.logger import logger

class Fuser:
    def __init__(self, provider: str = "mock"):
        self.llm = LLMManager(provider=provider)

    async def fuse(self, user_message: str, agent_responses: List[Dict]) -> str:
        """Combine multiple agent responses into one coherent answer."""
        if self.llm.provider == "mock":
            combined = " | ".join(
                [f"[{r['agent']}] {r['data']['message'] if isinstance(r['data'], dict) else str(r['data'])}" 
                for r in agent_responses])

            return combined

        prompt = (
            "Combine these agent responses into a concise and helpful summary.\n\n"
            f"User request: {user_message}\n\n"
        )
        for r in agent_responses:
            prompt += f"- {r['agent']}: {r['data']}\n"

        return await self.llm.run(prompt)
