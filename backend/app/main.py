import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.api.query import router as query_router
from app.core.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure SQLite fallback database is initialized if not present
    if not settings.sqlite_db_path.exists():
        from backend.db.init_sqlite import init_sqlite_database
        init_sqlite_database(settings.sqlite_db_path)
    yield


app = FastAPI(
    title="NexusDB — Agentic Enterprise AI Database Backend",
    description="Multi-agent natural language database query platform with self-correcting query execution.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:3000",
        "http://localhost:8000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query_router, prefix="/api", tags=["Queries"])


@app.get("/")
async def root():
    return {
        "name": "NexusDB Agentic AI Backend",
        "status": "online",
        "version": "1.0.0",
        "endpoints": {
            "query": "/api/query",
            "health": "/health",
            "stats": "/api/stats",
            "agents": "/api/agents",
            "audit": "/api/audit",
            "recent_queries": "/api/queries/recent",
        },
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "database": "online",
        "model": settings.gemini_model,
    }


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
