# llm/langchain_gemini.py
from langchain.llms.base import LLM
from llm.llm_manager import LLMManager
from typing import Optional, List
from pydantic import BaseModel, Field

class LangChainGemini(BaseModel):
    llm_manager: LLMManager = Field(default_factory=LLMManager)

    class Config:
        arbitrary_types_allowed = True

    @property
    def _llm_type(self) -> str:
        return "gemini"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """
        Standard sync call LangChain expects.
        """
        return prompt  # Or process output as needed

    async def classify_agents(self, message: str, registry_summary: str) -> list[str]:
        return await self.llm_manager.classify_agents(message, registry_summary)
