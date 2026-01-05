# from data.logger import logger
# from data.async_utils import gather_with_timeout
# from core.fuser import Fuser
# from core.selector import Selector
# import asyncio
# import importlib
# from typing import Dict, Any


# class Orchestrator:
#     def __init__(self, metadata_manager):
#         """
#         metadata_manager: loads agents_registry.json
#         """
#         self.metadata_manager = metadata_manager
#         self.selector = Selector(metadata_manager)
#         self.fuser = Fuser()
#         self.call_timeout = 5  # seconds per agent

#         # Cache agent instances
#         self._agents: Dict[str, Any] = {}

#         # 🔥 PRELOAD ALL AGENTS AT STARTUP
#         self._preload_agents()

#         # 🔁 START BACKGROUND AGENTS
#         self._start_background_agents()

#     # -------------------------
#     # Preload agents (heavy init here)
#     # -------------------------
#     def _preload_agents(self):
#         logger.info("Preloading all agents...")

#         for meta in self.metadata_manager.list_all():
#             try:
#                 module = importlib.import_module(meta.module)
#                 agent_cls = getattr(module, meta.class_name)

#                 agent = agent_cls()  # heavy RAG init happens ONCE
#                 self._agents[meta.name] = agent

#                 logger.info(f"Preloaded agent: {meta.name}")
#             except Exception as e:
#                 logger.error(f"Failed to preload agent {meta.name}: {e}")

#     # -------------------------
#     # Background agents
#     # -------------------------
#     def _start_background_agents(self):
#         for meta in self.metadata_manager.list_all():
#             if meta.name == "monitoring_agent":
#                 agent = self._agents.get(meta.name)
#                 if agent:
#                     logger.info("Starting MonitoringAgent in background")
#                     asyncio.create_task(agent.run_forever())

#     # -------------------------
#     # Agent getter (NO re-init)
#     # -------------------------
#     def _load_agent(self, meta):
#         """
#         Return already-preloaded agent instance
#         """
#         agent = self._agents.get(meta.name)
#         if not agent:
#             raise RuntimeError(f"Agent {meta.name} was not preloaded")
#         return agent

#     # -------------------------
#     # Main request handler
#     # -------------------------
#     async def handle_request(self, message: str):
#         logger.info(f"Handling user request: {message}")

#         # 1️⃣ Select agents
#         selected_metas = await self.selector.select_agents(message)

#         if not selected_metas:
#             return {"fused": "No suitable agents found for this request."}

#         logger.info(f"Selected agents: {[m.name for m in selected_metas]}")

#         # 2️⃣ Run agents concurrently
#         async def run_agent(meta):
#             agent = self._load_agent(meta)
#             return await agent.run(message)

#         tasks = [run_agent(m) for m in selected_metas]
#         responses = await gather_with_timeout(tasks, timeout=self.call_timeout)

#         # 3️⃣ Prepare responses
#         agent_responses = [
#             {
#                 "agent": meta.name,
#                 "ok": True,
#                 "data": {"message": resp},
#             }
#             for meta, resp in zip(selected_metas, responses)
#         ]

#         # 4️⃣ Fuse
#         fused = await self.fuser.fuse(message, agent_responses)

#         return {
#             "agents_called": [m.name for m in selected_metas],
#             "fused": fused,
#         }


from data.logger import logger
from data.async_utils import gather_with_timeout
from core.fuser import Fuser
from core.selector import Selector
import asyncio
import importlib
from typing import Dict, Any, List

class Orchestrator:
    def __init__(self, metadata_manager):
        """
        metadata_manager: loads agents_registry.json
        """
        self.metadata_manager = metadata_manager
        self.selector = Selector(metadata_manager)
        self.fuser = Fuser()
        self.call_timeout = 5  # seconds per agent

        # Cache agent instances
        self._agents: Dict[str, Any] = {}

        # 🔥 PRELOAD ALL AGENTS AT STARTUP
        self._preload_agents()

        # 🔁 START BACKGROUND AGENTS
        self._start_background_agents()

    # -------------------------
    # Preload agents (heavy init here)
    # -------------------------
    def _preload_agents(self):
        logger.info("Preloading all agents...")

        for meta in self.metadata_manager.list_all():
            try:
                module = importlib.import_module(meta.module)
                agent_cls = getattr(module, meta.class_name)

                agent = agent_cls()  # heavy RAG init happens ONCE
                self._agents[meta.name] = agent

                logger.info(f"Preloaded agent: {meta.name}")
            except Exception as e:
                logger.error(f"Failed to preload agent {meta.name}: {e}")

    # -------------------------
    # Background agents
    # -------------------------
    def _start_background_agents(self):
        pass
        # # for meta in self.metadata_manager.list_all():
        # #     if meta.name == "monitoring_agent":
        # #         agent = self._agents.get(meta.name)
        # #         if agent:
        # logger.info("Starting MonitoringAgent in background")
        # asyncio.create_task(monitoring_agent.run_forever())

    # -------------------------
    # Agent getter (NO re-init)
    # -------------------------
    def _load_agent(self, meta):
        """
        Return already-preloaded agent instance
        """
        agent = self._agents.get(meta.name)
        if not agent:
            raise RuntimeError(f"Agent {meta.name} was not preloaded")
        return agent

    # -------------------------
    # Main request handler (with agent-specific queries)
    # -------------------------
    async def handle_request(self, message: str):
        logger.info(f"Handling user request: {message}")

        # 1️⃣ Select agents (selector has LLM with memory)
        selected_metas = await self.selector.select_agents(message)

        if not selected_metas:
            no_agent_response = "No suitable agents found for this request."
            # Update memory in selector's LLM
            self.selector.llm.update_memory_with_response(no_agent_response)
            return {"fused": no_agent_response}

        logger.info(f"Selected agents: {[m.name for m in selected_metas]}")

        # 2️⃣ Generate agent-specific queries using LLM Manager
        agent_names = [m.name for m in selected_metas]
        registry = self.metadata_manager.list_all()
        registry_summary = "\n".join(
            f"{m.name}: {m.description}" for m in registry
        )
        
        agent_queries = await self.selector.llm.generate_agent_queries(
            message, 
            agent_names,
            registry_summary
        )

        # 3️⃣ Run agents concurrently with their specific queries
        async def run_agent(meta):
            agent = self._load_agent(meta)
            specific_query = agent_queries.get(meta.name, message)
            logger.info(f"🎯 Agent '{meta.name}' receiving query: '{specific_query}'")
            return await agent.run(specific_query)

        tasks = [run_agent(m) for m in selected_metas]
        responses = await gather_with_timeout(tasks, timeout=self.call_timeout)

        # 4️⃣ Prepare responses
        agent_responses = [
            {
                "agent": meta.name,
                "query": agent_queries.get(meta.name, message),
                "ok": True,
                "data": {"message": resp},
            }
            for meta, resp in zip(selected_metas, responses)
        ]

        # 5️⃣ Fuse responses
        fused = await self.fuser.fuse(message, agent_responses)

        # 🧠 6️⃣ Update memory with final response
        self.selector.llm.update_memory_with_response(fused)

        return {
            "agents_called": [m.name for m in selected_metas],
            "agent_queries": agent_queries,
            "original_query": message,
            "fused": fused,
        }

    def clear_memory(self):
        """Clear session memory for new conversation."""
        self.selector.llm.clear_memory()
        logger.info("Orchestrator memory cleared")