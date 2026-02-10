from core.metadata_manager import MetadataManager

import threading
from agents.monitoring_agent.monitoring_agent import MonitoringAgent


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



monitor_thread = None  # 👈 global guard

@app.on_event("startup")
def start_background_monitoring():
    global monitor_thread

    if monitor_thread is None:
        agent = MonitoringAgent()
        monitor_thread = threading.Thread(
            target=agent.start,  # infinite loop inside
            daemon=True
        )
        monitor_thread.start()

@app.post("/query")
async def handle_query(q: Query):
    return await orc.handle_request(q.message)


import json
import os
from fastapi import Body

APPROVAL_FILE = "storage/approval.json"
os.makedirs("storage", exist_ok=True)


@app.get("/approval")
def get_approval():
    try:
        with open(APPROVAL_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


@app.post("/approval")
def set_approval(data: dict = Body(...)):
    with open(APPROVAL_FILE, "w") as f:
        json.dump(data, f, indent=2)
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)