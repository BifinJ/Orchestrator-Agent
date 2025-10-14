import json
from models.schemas import AgentMetadata
from typing import List
from utils.logger import logger

class MetadataManager:
    def __init__(self, path: str = "data/agents_registry.json"):
        self.path = path
        self._registry = self._load()

    def _load(self) -> List[AgentMetadata]:
        with open(self.path, "r") as f:
            raw = json.load(f)
        metas = [AgentMetadata(**r) for r in raw]
        logger.info(f"Loaded {len(metas)} agents from metadata")
        return metas

    def list_all(self) -> List[AgentMetadata]:
        return self._registry
