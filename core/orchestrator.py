from .metadata_manager import MetadataManager
from .selector import Selector
from .fuser import Fuser
from utils.logger import logger
from utils.async_utils import gather_with_timeout
import importlib
import asyncio

class Orchestrator:
    def __init__(self, metadata_path: str = "data/agents_registry.json"):
        self.metadata = MetadataManager(metadata_path)
        self.selector = Selector(self.metadata)
        self.fuser = Fuser()
        self.call_timeout = 5  # seconds per agent

    async def handle_request(self, message: str):
        logger.info(f"Handling user request: {message}")

        # 1️⃣ Select agents to handle this message
        candidates = await self.selector.select_agents(message)
        logger.info("Selected agents: %s", [c.name for c in candidates])

        # 2️⃣ Run agents concurrently (locally)
        tasks = [self._call_agent(a, message) for a in candidates]
        responses = await gather_with_timeout(tasks, timeout=self.call_timeout)

        # 3️⃣ Fuse their outputs into a single summary
        fused = await self.fuser.fuse(message, responses)
        return {
            "agents_called": [a.name for a in candidates],
            "responses": responses,
            "fused": fused
        }

    async def _call_agent(self, agent_meta, message: str):
        """Dynamically import agent module and execute its handler."""
        try:
            module = importlib.import_module(agent_meta.module)
            if hasattr(module, "process"):
                func = module.process
                if asyncio.iscoroutinefunction(func):
                    result = await func(message)
                else:
                    result = func(message)
                return {"agent": agent_meta.name, "ok": True, "data": result}
            else:
                raise AttributeError("No 'process' function found in module")
        except Exception as e:
            logger.error(f"Error calling agent {agent_meta.name}: {e}")
            return {"agent": agent_meta.name, "ok": False, "data": {"error": str(e)}}
