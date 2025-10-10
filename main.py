from core.registry import AgentRegistry
from core.orchestrator import Orchestrator
from agents.api_agent import APIAgent
from agents.base_agent import BaseAgent

# Dummy agents
class StaticAgent(BaseAgent):
    def process(self, query):
        return "Operational excellence focuses on continuous improvement."

class SummaryAgent(BaseAgent):
    def process(self, query):
        return "Your workloads were stable with 99.9% uptime last week."

if __name__ == "__main__":
    registry = AgentRegistry()
    registry.register("api", APIAgent("API Agent"))
    registry.register("static", StaticAgent("Static Agent"))
    registry.register("summary", SummaryAgent("Summary Agent"))

    orch = Orchestrator(registry)
    print("=== MOYA Framework Prototype ===")

    while True:
        q = input("\nAsk MOYA ➜ ")
        if q.lower() in ["exit", "quit"]:
            break
        print("→", orch.route_query(q))
