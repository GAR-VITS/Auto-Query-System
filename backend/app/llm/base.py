"""
NexusDB LLM Client Protocol & Structured Return Types
Defines the standard protocol for LLM clients (GeminiClient, FakeLLM).
"""

from typing import Protocol, runtime_checkable, Any
from pydantic import BaseModel, Field


class IntentClassification(BaseModel):
    intent: str = Field(description="'query', 'action', or 'clarify'")
    action_name: str | None = Field(default=None, description="Action name if intent == 'action'")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Extracted parameters if action")
    clarify_question: str | None = Field(default=None, description="Specific clarifying question if clarify")
    confidence: float = 1.0


class GeneratedSql(BaseModel):
    sql: str
    rationale: str
    assumptions: list[str] = Field(default_factory=list)
    confidence: float = 1.0


class NarrativeResult(BaseModel):
    insight_text: str
    read_as: str = ""
    flags: list[str] = Field(default_factory=list)


@runtime_checkable
class LLMClient(Protocol):
    async def classify_intent(self, question: str) -> IntentClassification:
        ...

    async def generate_sql(self, question: str, context: Any) -> GeneratedSql:
        ...

    async def repair_sql(self, question: str, context: Any, attempts: list[Any]) -> GeneratedSql:
        ...

    async def narrate(self, question: str, stats: dict[str, Any]) -> NarrativeResult:
        ...
