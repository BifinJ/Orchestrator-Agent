from .base_agent import BaseAgent
import random

class APIAgent(BaseAgent):
    def __init__(self, name="API Agent"):
        super().__init__(name)
        self.notifications = [
            {"type": "security", "msg": "IAM role unused for 30 days"},
            {"type": "cost", "msg": "EC2 instance i-02 exceeded budget by 15%"},
            {"type": "performance", "msg": "Load balancer latency increased"}
        ]

    def process(self, query: str) -> str:
        q = query.lower()
        if "notification" in q or "alert" in q:
            notes = "\n".join([f"- {n['type'].title()}: {n['msg']}"
                               for n in self.notifications])
            return f"Recent notifications:\n{notes}"
        elif "cost" in q or "spend" in q:
            val = random.randint(400, 600)
            return f"Your current monthly cost is approximately ${val}."
        else:
            return "API agent couldn’t find matching data."
