"""RepoMind FastAPI Application — Main HTTP entrypoint."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.manager import manager
from backend.api.models import HealthResponse
from backend.api.routes import router as investigation_router
from backend.db.supabase import db_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI application lifespan: initialize database pool & checkpointer."""
    await db_manager.initialize()
    manager.set_checkpointer(db_manager.checkpointer)
    yield
    await db_manager.close()


app = FastAPI(
    title="RepoMind API",
    description="Autonomous, read-only local repository investigation agent powered by LangGraph and Google Gemini.",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS Configuration ─────────────────────────────────────────────────────────
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
if os.getenv("ALLOW_ALL_CORS", "true").lower() == "true":
    origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health Check ───────────────────────────────────────────────────────────────
@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["system"],
    summary="API Health Status",
)
async def health_check():
    """Verify backend API is responsive and report database mode."""
    return HealthResponse(
        status="ok",
        version="0.1.0",
    )


# ── Mount Investigation Routes ─────────────────────────────────────────────────
app.include_router(investigation_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
