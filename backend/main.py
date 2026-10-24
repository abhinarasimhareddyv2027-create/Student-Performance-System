import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import academics, analytics, auth, profiles, reports, users
from database.connection import initialize_database
from database import academic_models  # noqa: F401


def create_app(initialize_on_startup: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        if initialize_on_startup:
            initialize_database()
        yield

    app = FastAPI(title="Student Performance System API", version="1.0.0", lifespan=lifespan)
    allowed_origins = [
        origin.strip()
        for origin in os.environ.get("SPS_CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_origin_regex=r"https://[a-zA-Z0-9-]+-5173\.app\.github\.dev",
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-Requested-With"],
    )
    app.include_router(auth.router, prefix="/api")
    app.include_router(profiles.router, prefix="/api")
    app.include_router(academics.router, prefix="/api")
    app.include_router(analytics.router, prefix="/api")
    app.include_router(reports.router, prefix="/api")
    app.include_router(users.router, prefix="/api")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()