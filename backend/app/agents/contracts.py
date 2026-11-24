"""
NexusDB Pydantic JSON Handoff Contracts
Enforces strict zero-state leakage between Orchestrator, Query Agent, Analysis Agent, and Viz Agent.
"""

from typing import Any, Literal
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str
    user_id: str = "demo_user"
    role: str = "viewer"
    request_id: str
    branch_id: int | None = None
    schema_context: str | None = None


class QueryResult(BaseModel):
    sql: str
    columns: list[str] = Field(default_factory=list)
    rows: list[list[Any]] = Field(default_factory=list)
    row_count: int = 0
    truncated: bool = False
    attempts: list[dict[str, Any]] = Field(default_factory=list)
    interpretation: str = ""


class AnalysisResult(BaseModel):
    stats: dict[str, Any] = Field(default_factory=dict)
    insight_text: str = ""
    read_as: str = ""
    flags: list[str] = Field(default_factory=list)


class DatasetSpec(BaseModel):
    label: str
    data: list[float | int]
    backgroundColor: str | list[str] | None = None
    borderColor: str | None = None
    borderWidth: int | None = 1


class VizSpec(BaseModel):
    chart_type: Literal["bar", "line", "doughnut", "kpi", "none"]
    labels: list[str] = Field(default_factory=list)
    datasets: list[DatasetSpec] = Field(default_factory=list)
    kpi_value: str | float | int | None = None
    kpi_label: str | None = None
    reason: str = ""
