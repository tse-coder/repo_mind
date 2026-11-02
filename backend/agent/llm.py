"""
LLM factory and utility functions for RepoMind.

Configures Google Gemini via langchain-google-genai.
"""

from __future__ import annotations

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.config import GOOGLE_API_KEY, LLM_MODEL_NAME, LLM_TEMPERATURE


def get_llm(temperature: float = LLM_TEMPERATURE, model: str = LLM_MODEL_NAME) -> ChatGoogleGenerativeAI:
    """Return an initialized Google Gemini LLM instance."""
    if not GOOGLE_API_KEY:
        raise ValueError(
            "GOOGLE_API_KEY is not set. Please set GOOGLE_API_KEY or GEMINI_API_KEY in your .env file."
        )

    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=GOOGLE_API_KEY,
        temperature=temperature,
    )
