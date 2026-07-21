"""FastAPI application entry point for the novel generation platform.

Handles application lifecycle (startup/shutdown), middleware configuration,
and API route registration.
"""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

from app.api.v1.chapters import router as chapters_router  # noqa: E402
from app.api.v1.characters import router as characters_router  # noqa: E402
from app.api.v1.chat import router as chat_router  # noqa: E402
from app.api.v1.outlines import router as outlines_router  # noqa: E402
from app.api.v1.projects import router as projects_router  # noqa: E402
from app.api.v1.reviews import router as reviews_router  # noqa: E402
from app.api.v1.skills import router as skills_router  # noqa: E402
from app.api.v1.world import router as world_router  # noqa: E402
from app.config import settings  # noqa: E402
from app.db.checkpointer import close_checkpointer, init_checkpointer  # noqa: E402
from app.db.connection import init_db  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Manage application lifespan events.

    Initializes the database and LangGraph checkpointer on startup,
    and cleans up the checkpointer on shutdown.

    Args:
        app: The FastAPI application instance.

    Yields:
        None after initialization completes.
    """
    await init_db()
    await init_checkpointer()
    yield
    await close_checkpointer()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        A fully configured FastAPI application with CORS middleware
        and all API v1 routes registered.
    """
    app = FastAPI(
        title="Novel Generator API",
        description="AI-powered web novel generation platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(projects_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(world_router, prefix="/api/v1")
    app.include_router(characters_router, prefix="/api/v1")
    app.include_router(outlines_router, prefix="/api/v1")
    app.include_router(chapters_router, prefix="/api/v1")
    app.include_router(reviews_router, prefix="/api/v1")
    app.include_router(skills_router, prefix="/api/v1")

    app.add_api_route("/health", health_check, methods=["GET"])

    return app


async def health_check() -> dict[str, str]:
    """Return the health status of the API.

    Returns:
        A dict with a single key ``status`` set to ``"healthy"``.
    """
    return {"status": "healthy"}


app = create_app()
