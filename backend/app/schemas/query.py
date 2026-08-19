from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    voice: bool = False


class QueryResult(BaseModel):
    id: str
    question: str
    sql: str
    columns: List[str]
    rows: List[Dict[str, Any]]
    rowCount: int
    executionTimeMs: float
    analysis: Optional[str] = None
    corrections: int = 0
    timestamp: str


class QueryResponse(BaseModel):
    success: bool
    result: Optional[QueryResult] = None
    error: Optional[str] = None


class DashboardStatItem(BaseModel):
    label: str
    value: Any
    change: Optional[str] = None
    trend: Optional[str] = None


class AgentInfoItem(BaseModel):
    id: str
    name: str
    description: str
    status: str
    lastRun: Optional[str] = None


class AuditEntryItem(BaseModel):
    id: str
    timestamp: str
    action: str
    status: str
    agent: str
    user: str
    description: str
    reasoning: str
    affectedRecords: Optional[int] = None
