"""
RepoMind configuration — loads environment variables and provides shared settings.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# ── LLM ────────────────────────────────────────────────────────────────────────
GOOGLE_API_KEY = (
    os.getenv("GOOGLE_API_KEY")
    or os.getenv("GEMINI_API_KEY")
    or os.getenv("GOOGLE_GENERATIVE_AI_API_KEY", "")
)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Provider selection: "groq" or "gemini". Defaults to "groq" if GROQ_API_KEY is set.
LLM_PROVIDER = os.getenv(
    "LLM_PROVIDER",
    "groq" if GROQ_API_KEY else "gemini"
).lower()

_default_model = "openai/gpt-oss-120b" if LLM_PROVIDER == "groq" else "gemini-1.5-flash"
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", _default_model)
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))

# ── Defaults & Filters ─────────────────────────────────────────────────────────
DEFAULT_EXCLUDED_DIRS = frozenset({
    ".git",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "venv",
    ".venv",
    "dist",
    "build",
    ".idea",
    ".vscode",
})

# ── Agent Defaults ─────────────────────────────────────────────────────────────
DEFAULT_MAX_STEPS = int(os.getenv("DEFAULT_MAX_STEPS", "20"))
DEFAULT_MAX_CLARIFICATIONS = int(os.getenv("DEFAULT_MAX_CLARIFICATIONS", "2"))
MAX_RETRIES_PER_STRATEGY = 2
READ_FILE_MAX_LINES = 200
SEARCH_MAX_RESULTS = 30

# ── Vector Store ───────────────────────────────────────────────────────────────
CHROMA_PERSIST_DIR = str(PROJECT_ROOT / "chroma_data")
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
