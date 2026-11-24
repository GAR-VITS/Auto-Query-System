"""
NexusDB Schema Catalog & Semantic Retrieval Playground Endpoints
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.deps import get_current_user
from app.governance.rbac import UserSession
from app.memory.catalog import get_catalog_snapshot
from app.memory.store import get_schema_memory

router = APIRouter(prefix="/schema", tags=["Schema"])


class PlaygroundRequest(BaseModel):
    question: str
    top_k: int = 8


@router.get("")
async def get_schema_catalog(user: UserSession = Depends(get_current_user)):
    cat = get_catalog_snapshot()
    tables_summary = []
    for tbl_name, tbl in cat.tables.items():
        cols = [
            {
                "name": c.name,
                "type": c.data_type,
                "is_pk": c.is_primary_key,
                "comment": c.comment,
                "sample_values": c.sample_values,
            }
            for c in tbl.columns.values()
        ]
        fks = [
            {
                "from_column": fk.from_column,
                "to_table": fk.to_table,
                "to_column": fk.to_column,
                "join_hint": fk.join_hint,
            }
            for fk in tbl.foreign_keys
        ]
        tables_summary.append({
            "name": tbl.name,
            "schema": tbl.schema_name,
            "comment": tbl.comment,
            "columns": cols,
            "foreign_keys": fks,
        })

    return {
        "catalog_hash": cat.catalog_hash,
        "total_tables": len(tables_summary),
        "tables": tables_summary,
    }


@router.post("/playground")
async def retrieval_playground(req: PlaygroundRequest, user: UserSession = Depends(get_current_user)):
    mem = get_schema_memory()
    ctx = mem.retrieve(req.question, top_k=req.top_k)

    return {
        "question": req.question,
        "retrieved_tables": ctx.retrieved_tables,
        "schema_slices": ctx.schema_slices,
        "glossary_rules": ctx.glossary_rules,
        "full_schema_chars": ctx.full_schema_chars,
        "context_chars": ctx.context_chars,
        "context_saved_pct": ctx.context_saved_pct,
    }
