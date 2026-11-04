"""
LLM factory and utility functions for RepoMind.

Supports:
- Groq via langchain-groq (ultra-fast, high free-tier rate limits: 30 RPM / 100k TPM)
- Google Gemini via langchain-google-genai
"""

from __future__ import annotations

import logging

from langchain_core.language_models.chat_models import BaseChatModel

from backend.config import (
    GOOGLE_API_KEY,
    GROQ_API_KEY,
    LLM_MODEL_NAME,
    LLM_PROVIDER,
    LLM_TEMPERATURE,
)

logger = logging.getLogger("repomind.llm")


def _create_groq_llm(temperature: float, model: str | None = None) -> BaseChatModel:
    """Create a Groq Chat instance using langchain-groq."""
    from langchain_groq import ChatGroq

    api_key = GROQ_API_KEY
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is not set. Please set GROQ_API_KEY in your .env file."
        )
    target_model = model or (
        LLM_MODEL_NAME
        if any(kw in LLM_MODEL_NAME.lower() for kw in ("llama", "qwen", "openai", "gpt", "mixtral", "gemma"))
        else "openai/gpt-oss-120b"
    )
    return ChatGroq(
        model=target_model,
        groq_api_key=api_key,
        temperature=temperature,
    )


def _create_gemini_llm(temperature: float, model: str | None = None) -> BaseChatModel:
    """Create a Google Gemini Chat instance using langchain-google-genai."""
    from langchain_google_genai import ChatGoogleGenerativeAI

    if not GOOGLE_API_KEY:
        raise ValueError(
            "GOOGLE_API_KEY is not set. Please set GOOGLE_API_KEY or GEMINI_API_KEY in your .env file."
        )
    target_model = model or (
        LLM_MODEL_NAME if "gemini" in LLM_MODEL_NAME.lower() else "gemini-1.5-flash"
    )
    return ChatGoogleGenerativeAI(
        model=target_model,
        google_api_key=GOOGLE_API_KEY,
        temperature=temperature,
    )


def get_llm(
    temperature: float = LLM_TEMPERATURE,
    model: str | None = None,
    provider: str | None = None,
) -> BaseChatModel:
    """Return an initialized LLM instance (Groq or Gemini)."""
    selected_provider = (provider or LLM_PROVIDER).lower()

    if selected_provider == "groq":
        return _create_groq_llm(temperature=temperature, model=model)
    elif selected_provider in ("gemini", "google"):
        return _create_gemini_llm(temperature=temperature, model=model)
    else:
        # Fallback to whatever provider has an API key configured
        if GROQ_API_KEY:
            return _create_groq_llm(temperature=temperature, model=model)
        return _create_gemini_llm(temperature=temperature, model=model)
