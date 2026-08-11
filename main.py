"""
Entrypoint. Run with:

    uvicorn app.main:app --reload

On startup, indexes the current Postgres schema into ChromaDB so the
Query Agent has schema context available from the first request.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.database import fetch_schema_snapshot, schema_snapshot_to_documents
from app.embeddings import index_schema_documents

app = FastAPI(
    title="Natural Language Database Navigation Platform",
    description=(
        "Self-correcting multi-agent framework for querying a business "
        "database in plain English (or voice)."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this before production (React frontend origin only)
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def index_schema_on_startup() -> None:
    try:
        snapshot = fetch_schema_snapshot()
        documents = schema_snapshot_to_documents(snapshot)
        index_schema_documents(documents)
    except Exception as e:  # noqa: BLE001
        # Don't crash the server if Postgres isn't reachable yet at boot —
        # /schema/reindex can be called manually once it is.
        print(f"[startup] schema indexing skipped: {e}")
