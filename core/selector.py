# core/selector.py
from typing import List
from models.schemas import AgentMetadata
from llm.llm_manager import LLMManager
from utils.logger import logger

class Selector:
    def __init__(self, metadata_mgr):
        self.metadata = metadata_mgr
        self.llm = LLMManager(provider="gemini-2.5-flash-lite")

    async def select_agents(self, message: str, top_k: int = 3) -> List[AgentMetadata]:
        registry = self.metadata.list_all()
        if not registry:
            logger.warning("No agents registered.")
            return []

        summary = "\n".join([f"{m.name}: {', '.join(m.description)}" for m in registry])

        # Get classification from Gemini
        agent_names = await self.llm.classify_agents(message, summary)
        print("Summary",summary)
        if not agent_names:
            logger.warning("Gemini returned no matches, fallback to keyword.")
            return self._fallback_keyword(message, registry, top_k)

        selected = [m for m in registry if m.name in agent_names][:top_k]
        logger.info(f"Gemini selected agents: {[m.name for m in selected]}")
        return selected

    def _fallback_keyword(self, message: str, registry, top_k: int):
        msg = message.lower()
        scored = []
        for m in registry:
            score = sum(tok in msg for cap in m.description for tok in cap.lower().split())
            if score > 0:
                scored.append((m, score))
        scored.sort(key=lambda x: -x[1])
        return [m for m, _ in scored[:top_k]]
