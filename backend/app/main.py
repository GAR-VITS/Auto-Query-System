"""
NexusDB FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.query import router as query_router
from app.api.actions import router as actions_router
from app.api.audit import router as audit_router
from app.api.schema import router as schema_router
from app.api.metrics import router as metrics_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB and index schema memory on startup
    from app.db.session import init_database
    from app.memory.store import get_schema_memory
    init_database()
    get_schema_memory()
    yield


app = FastAPI(
    title="NexusDB",
    description="Self-correcting multi-agent SQL & governed write-back platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list if settings.cors_origins_list else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(query_router)
app.include_router(actions_router)
app.include_router(audit_router)
app.include_router(schema_router)
app.include_router(metrics_router)


@app.get("/")
async def root():
    return {
        "name": "NexusDB Agentic Platform",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
