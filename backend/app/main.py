"""MarkLoss Backend Application."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.errors import register_error_handlers
from app.routers import grade, health, hint, problems, transcribe

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("markloss")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting MarkLoss API server (DEMO_MODE=%s, Provider=%s)", settings.is_demo_mode, settings.LLM_PROVIDER)
    yield
    logger.info("Shutting down MarkLoss API server")


app = FastAPI(
    title="MarkLoss API",
    description="Step-level AI examiner for handwritten physics and math answers.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register custom error handlers
register_error_handlers(app)

# Include Routers
app.include_router(health.router)
app.include_router(problems.router)
app.include_router(transcribe.router)
app.include_router(grade.router)
app.include_router(hint.router)

# Mount static files (samples and production frontend)
from pathlib import Path
from fastapi.staticfiles import StaticFiles

project_root = Path(__file__).resolve().parent.parent.parent
samples_images_dir = project_root / "samples" / "images"
if samples_images_dir.exists():
    app.mount("/samples/images", StaticFiles(directory=str(samples_images_dir)), name="sample_images")

frontend_dist = project_root / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
