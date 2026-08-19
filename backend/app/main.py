import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Automatically ensure both backend directory and root directory are in sys.path
backend_dir = Path(__file__).resolve().parent.parent
root_dir = backend_dir.parent
for d in [str(backend_dir), str(root_dir)]:
    if d not in sys.path:
        sys.path.insert(0, d)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

try:
    from app.api.query import router as query_router
    from app.core.config import get_settings
except ImportError:
    from backend.app.api.query import router as query_router
    from backend.app.core.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure SQLite fallback database is initialized if not present
    if not settings.sqlite_db_path.exists():
        try:
            from db.init_sqlite import init_sqlite_database
        except ImportError:
            from backend.db.init_sqlite import init_sqlite_database
        init_sqlite_database(settings.sqlite_db_path)
    yield


app = FastAPI(
    title="NexusDB — Agentic Enterprise AI Database Backend",
    description="Multi-agent natural language database query platform with self-correcting query execution.",
    version="1.0.0",
    lifespan=lifespan,
)

# Robust CORS configuration for local and cloud deployment (Render, Vercel, Netlify, custom domains)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins if settings.allowed_origins != ["*"] else ["*"],
    allow_origin_regex=r"https?://.*",
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
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
