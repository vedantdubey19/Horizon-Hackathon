from fastapi import APIRouter
from app.config import settings

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check():
    """Service health and operational status."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "demo_mode": settings.is_demo_mode,
        "provider": settings.LLM_PROVIDER,
    }
