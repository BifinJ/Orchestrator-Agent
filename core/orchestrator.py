class Orchestrator:
    def __init__(self, registry):
        self.registry = registry

    def route_query(self, query: str):
        q = query.lower()
        if "cost" in q or "spend" in q:
            agent = self.registry.get("api")
        elif "summarize" in q or "overview" in q:
            agent = self.registry.get("summary")
        elif "explain" in q or "what is" in q or "define" in q:
            agent = self.registry.get("static")
        else:
            return "Sorry, I don't understand that request yet."

        return agent.process(query)
