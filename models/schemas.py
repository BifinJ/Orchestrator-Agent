from pydantic import BaseModel

class AgentMetadata(BaseModel):
    name: str
    module: str
    description: str 
    class_name: str
