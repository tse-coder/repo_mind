"""
RepoMind FastAPI Application — Main HTTP entrypoint.
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.models import HealthResponse
from backend.api.routes import router as investigation_router

app = FastAPI(
    title="RepoMind API",
    description="Autonomous, read-only local repository investigation agent powered by LangGraph and Google Gemini.",
    version="0.1.0",
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
    """Verify backend API is responsive."""
    return HealthResponse(status="ok", version="0.1.0")


# ── Mount Investigation Routes ─────────────────────────────────────────────────
app.include_router(investigation_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
