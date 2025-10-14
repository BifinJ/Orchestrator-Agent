# main.py
from fastapi import FastAPI
from core.orchestrator import Orchestrator
from pydantic import BaseModel

app = FastAPI(title="Orchestrator Agent")
orc = Orchestrator()

class Query(BaseModel):
    message: str

@app.post("/query")
async def handle_query(q: Query):
    return await orc.handle_request(q.message)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
