# core/tool_loader.py
from langchain.tools import Tool # type: ignore
import importlib
from models.schemas import AgentMetadata
from typing import List

def create_tools(metadata: List[AgentMetadata]) -> list[Tool]:
    tools = []
    for agent_meta in metadata:
        module = importlib.import_module(agent_meta.module)   # use .module from schema
        cls = getattr(module, agent_meta.class_name)          # use .class_name from schema
        instance = cls()                                      # instantiate once
        tool = Tool(
            name=agent_meta.name,
            func=lambda query, inst=instance: inst.process(query),
            description=agent_meta.description or ""
        )
        tools.append(tool)
    return tools
