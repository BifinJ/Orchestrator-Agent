from pydantic import BaseModel
from typing import List

class AgentMetadata(BaseModel):
    name: str
    capabilities: List[str]
    module: str
