from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.health import router as health_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure local database and seed exist on startup if in demo mode
    from app.db.session import init_database
    init_database()
    yield


app = FastAPI(
    title="NexusDB",
    description="Self-correcting multi-agent SQL & governed write-back platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, tags=["Health"])


@app.get("/")
async def root():
    return {
        "name": "NexusDB API",
        "status": "online",
        "docs": "/docs",
        "health": "/health",
    }
