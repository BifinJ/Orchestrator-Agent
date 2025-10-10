class BaseAgent:
    def __init__(self, name):
        self.name = name

    def process(self, query: str) -> str:
        raise NotImplementedError("Each agent must implement process()")
