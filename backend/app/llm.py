"""LLM factory — wraps ChatOpenRouter with a ChatOpenAI fallback.

Cached on first call so we don't reconstruct the LangChain client + httpx
connection pool on every agent instantiation. Within a single request the
same model string returns the same instance (which is process-wide safe
for langchain chat models).
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Any


@lru_cache(maxsize=4)
def _build_llm(model: str, api_key: str | None) -> Any:
    try:
        from langchain_openrouter import ChatOpenRouter  # type: ignore[import]
        return ChatOpenRouter(model=model, api_key=api_key, temperature=0.1)
    except ImportError:
        from langchain_openai import ChatOpenAI  # type: ignore[import]
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.1,
        )


def get_llm(model: str | None = None) -> Any:
    """Return a (cached) LangChain chat model pointed at OpenRouter."""
    resolved_model: str = model or os.getenv(
        "OPENROUTER_MODEL", "google/gemini-2.5-flash"
    )
    api_key: str | None = os.getenv("OPENROUTER_API_KEY")
    return _build_llm(resolved_model, api_key)
