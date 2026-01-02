from .base_agent import BaseAgent

class DummyAgent(BaseAgent):
    name = "dummy_agent"
    description = "A dummy placeholder agent"

    def __init__(self):
        super().__init__(self.name, self.description)

    async def run(self, message: str, context: dict = None):
        return f"Dummy processed: {message}"
