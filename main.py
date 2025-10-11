from fastapi import FastAPI
from pydantic import BaseModel
from workflows.orchestrator_flow import orchestrator_flow

app = FastAPI(title="Cloud Orchestrator Agent")

class Query(BaseModel):
    prompt: str

@app.post("/query")
def query_agent(data: Query):
    result = orchestrator_flow(data.prompt)
    return {"response": result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
