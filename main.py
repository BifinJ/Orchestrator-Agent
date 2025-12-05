# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from core.orchestrator import Orchestrator
from core.metadata_manager import MetadataManager
from core.tool_loader import create_tools
from fastapi.middleware.cors import CORSMiddleware

# FastAPI app
app = FastAPI(title="Orchestrator Agent")

origins = [
    "http://localhost",
    "http://127.0.0.1",
    "http://127.0.0.1:5500",
    "null"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,     
    allow_credentials=True,
    allow_methods=["*"],     
    allow_headers=["*"],     
)


# 1️⃣ Load agent metadata once
metadata_manager = MetadataManager("data/agents_registry.json")
metadata = metadata_manager.list_all()

# 2️⃣ Preload all Tools once at startup
tools = create_tools(metadata)

# 3️⃣ Initialize orchestrator with preloaded Tools
orc = Orchestrator(tools=tools)

# Request model
class Query(BaseModel):
    message: str

# API endpoint
@app.post("/query")
async def handle_query(q: Query):
    return await orc.handle_request(q.message)

# Run FastAPI server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
