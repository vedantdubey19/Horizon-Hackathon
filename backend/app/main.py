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
import re
from fastapi import Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

project_root = Path(__file__).resolve().parent.parent.parent
backend_dir = Path(__file__).resolve().parent.parent

# Resolve samples images directory from candidate paths
samples_images_candidates = [
    project_root / "samples" / "images",
    backend_dir / "samples" / "images",
    Path.cwd() / "samples" / "images",
    Path.cwd() / "backend" / "samples" / "images",
]
for p in samples_images_candidates:
    if p.exists():
        app.mount("/samples/images", StaticFiles(directory=str(p)), name="sample_images")
        break

# Resolve production frontend dist directory
frontend_dist_candidates = [
    project_root / "frontend" / "dist",
    backend_dir / "frontend" / "dist",
    Path.cwd() / "frontend" / "dist",
]
mounted_frontend = False
for f_dist in frontend_dist_candidates:
    if f_dist.exists() and (f_dist / "index.html").exists():
        index_html = f_dist / "index.html"

        @app.exception_handler(404)
        async def spa_404_handler(request: Request, exc):
            if not request.url.path.startswith("/api/") and index_html.exists():
                return FileResponse(index_html)
            return JSONResponse({"detail": "Not Found"}, status_code=404)

        app.mount("/", StaticFiles(directory=str(f_dist), html=True), name="frontend")
        mounted_frontend = True
        break

if not mounted_frontend:
    @app.get("/")
    async def root_info():
        return {
            "name": "MarkLoss API",
            "status": "online",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/api/health",
            "message": "MarkLoss API backend is running.",
        }


class NormalizePathASGIMiddleware:
    """Normalize consecutive slashes in request path (e.g. //api/health -> /api/health)."""

    def __init__(self, asgi_app):
        self.asgi_app = asgi_app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope.get("path", "")
            if "//" in path:
                scope["path"] = re.sub(r"/+", "/", path)
                raw_path = scope.get("raw_path", b"")
                if b"//" in raw_path:
                    scope["raw_path"] = re.sub(rb"/+", rb"/", raw_path)
        await self.asgi_app(scope, receive, send)


# Wrap FastAPI app with ASGI normalizer
app = NormalizePathASGIMiddleware(app)
