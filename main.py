from core.metadata_manager import MetadataManager


# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from core.orchestrator import Orchestrator
from agents.dummy_agent import DummyAgent
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="MAS Orchestrator")

origins = [
    "http://localhost",
    "http://127.0.0.1",
    "http://127.0.0.1:5500",
    "null"
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

metadata_manager = MetadataManager("data/agents_registry.json")
orc = Orchestrator(metadata_manager)


class Query(BaseModel):
    message: str



#@app.on_event("startup")
#async def startup_event():
#    """Runs ONCE when FastAPI starts"""
#    await orc.start_background_agents()
    
@app.post("/query")
async def handle_query(q: Query):
    return await orc.handle_request(q.message)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
