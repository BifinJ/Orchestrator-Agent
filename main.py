from fastapi import FastAPI
from pydantic import BaseModel
from workflows.orchestrator_flow import orchestrator_flow

from core.registry import AgentRegistry
from core.orchestrator import Orchestrator
from agents.static_agent import StaticAgent
from agents.summary_agent import SummaryAgent
from agents.api_agent import APIAgent

app = FastAPI(title="Cloud Orchestrator Agent")

class Query(BaseModel):
    prompt: str

@app.post("/query")
def query_agent(data: Query):
    result = orchestrator_flow(data.prompt)
    return {"response": result}

@app.get("/health")
def health_check():
    return "healthy"

if __name__ == "__main__":
    registry = AgentRegistry()
    registry.register("static", StaticAgent())
    registry.register("summary", SummaryAgent())
    registry.register("api", APIAgent())
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)




