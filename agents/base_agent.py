# agents/base_agent.py
# base_agent.py
class BaseAgent:
    def __init__(self, name: str, description: str = ""):
        """
        Base class for all agents.

        Args:
            name: Unique name of the agent (matches metadata registry)
            description: Short description or keywords for selection
        """
        self.name = name
        self.description = description
        
    async def run(self, message: str, context: dict = None):
        """
        Process a message and optionally update/use context.

        Args:
            message: user query or input
            context: a dict to store agent-specific state
        """
        context = context or {}
        # agent logic here
        return "some response"
