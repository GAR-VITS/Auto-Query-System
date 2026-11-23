from fastapi import APIRouter
from app.config import get_settings

router = APIRouter()


@router.get("/health")
async def health_check():
    settings = get_settings()
    return {
        "status": "healthy",
        "service": "NexusDB Agentic Core",
        "version": "1.0.0",
        "demo_mode": settings.demo_mode,
        "model": settings.gemini_model,
        "max_retries": settings.max_retries,
        "row_cap": settings.row_cap,
    }
