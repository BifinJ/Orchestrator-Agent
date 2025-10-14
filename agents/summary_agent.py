from .base_agent import BaseAgent
import json
from statistics import mean

class SummaryAgent(BaseAgent):
    def __init__(self, name="Summary Agent"):
        super().__init__(name)
        with open("data/logs.json", "r") as f:
            self.logs = json.load(f)

    def process(self, query: str) -> str:
        uptimes = [l["uptime"] for l in self.logs]
        costs = [l["cost"] for l in self.logs]

        avg_uptime = mean(uptimes)
        total_cost = sum(costs)
        return (f"Last {len(self.logs)} days summary:\n"
                f"• Avg uptime: {avg_uptime:.2f}%\n"
                f"• Total cost: ${total_cost:.2f}\n"
                f"• Trend: {'increasing' if costs[-1]>costs[0] else 'decreasing'}")
