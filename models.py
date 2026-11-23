"""
Pydantic schemas shared across the API layer and agents.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class QueryInputType(str, Enum):
    TEXT = "text"
    VOICE = "voice"


class UserQueryRequest(BaseModel):
    """What the frontend sends to POST /query."""
    query_text: Optional[str] = Field(
        None, description="Natural language question, if typed."
    )
    input_type: QueryInputType = QueryInputType.TEXT
    user_id: str = Field(..., description="Used for role-based permission checks later.")
    want_analysis: bool = Field(
        False, description="If true, also run the Analysis Agent (pandas/seaborn) on the result."
    )


class SQLAttempt(BaseModel):
    """One iteration of the self-correction loop — kept for transparency/debugging."""
    attempt_number: int
    sql: str
    error: Optional[str] = None
    succeeded: bool = False


class QueryAgentResult(BaseModel):
    final_sql: Optional[str]
    attempts: list[SQLAttempt]
    rows: list[dict[str, Any]] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list)
    row_count: int = 0
    succeeded: bool = False
    error: Optional[str] = None


class AnalysisResult(BaseModel):
    summary_stats: dict[str, Any] = Field(default_factory=dict)
    chart_base64_png: Optional[str] = None
    chart_description: Optional[str] = None


class UserQueryResponse(BaseModel):
    original_query: str
    generated_sql: Optional[str]
    sql_attempts: list[SQLAttempt]
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    natural_language_answer: str
    analysis: Optional[AnalysisResult] = None
    success: bool
    error: Optional[str] = None
