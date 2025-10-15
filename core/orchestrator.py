# core/orchestrator.py
from utils.logger import logger
from utils.async_utils import gather_with_timeout
from core.fuser import Fuser
import asyncio
from langchain.tools import Tool
from typing import List

class Orchestrator:
    def __init__(self, tools: List[Tool]):
        """
        tools: preloaded list of LangChain Tool objects (one per agent)
        """
        self.tools = tools
        self.fuser = Fuser()
        self.call_timeout = 5  # seconds per agent

    async def handle_request(self, message: str):
        logger.info(f"Handling user request: {message}")

        # 1️⃣ Select agents to handle this message
        # Filter tools by names returned from Gemini classification
        registry_summary = "\n".join([f"{t.name}: {t.description}" for t in self.tools])
        from llm.gemini import LangChainGemini
        llm = LangChainGemini()
        selected_agent_names = await llm.classify_agents(message, registry_summary)
        logger.info(f"Selected agents: {selected_agent_names}")

        # Filter the tools to only selected ones
        candidates = [t for t in self.tools if t.name in selected_agent_names]

        # 2️⃣ Run agents concurrently
        async def run_tool(tool: Tool):
            if asyncio.iscoroutinefunction(tool.func):
                return await tool.func(message)
            else:
                return tool.func(message)

        tasks = [run_tool(t) for t in candidates]
        responses = await gather_with_timeout(tasks, timeout=self.call_timeout)

        # Wrap responses for fuser
        agent_responses = [{"agent": t.name, "ok": True, "data": {"message": r}}
                           for t, r in zip(candidates, responses)]

        # 3️⃣ Fuse their outputs into a single summary
        fused = await self.fuser.fuse(message, agent_responses)

        return {
            "agents_called": [t.name for t in candidates],
            "responses": agent_responses,
            "fused": fused
        }
