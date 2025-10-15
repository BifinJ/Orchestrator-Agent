from pydantic import BaseModel

class AgentMetadata(BaseModel):
    name: str
    module: str
    description: str | None = None
    class_name: str  # add this
