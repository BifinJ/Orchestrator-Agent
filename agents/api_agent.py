from .base_agent import BaseAgent

class APIAgent(BaseAgent):
    def process(self, query):
        return "You spent $512 this month on EC2 and S3 combined."
