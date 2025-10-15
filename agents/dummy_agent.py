# agents/dummy_agent.py
from .base_agent import BaseAgent

class DummyAgent(BaseAgent):
    def __init__(self, name="Dummy Agent"):
        super().__init__(name)

    def process(self, query: str) -> str:
        # Just return a dummy response for testing
        return f"Dummy response for query: '{query}'"

# Create a module-level callable for orchestrator
agent_instance = DummyAgent()

def process(query: str):
    return agent_instance.process(query)
