"""Application configuration via pydantic-settings."""
from __future__ import annotations

import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    openrouter_api_key: str = Field(
        default="",
        description="OpenRouter API key (sk-or-v1-...)",
    )
    openrouter_model: str = Field(
        default="google/gemini-2.5-flash",
        description="Model ID to use via OpenRouter",
    )

    # Storage
    data_dir: Path = Field(
        default=Path("./data"),
        description="Directory for per-session SQLite DBs and LangGraph checkpoints",
    )

    # Server
    frontend_port: int = Field(
        default=5173,
        description="Vite dev server port — whitelisted in CORS",
    )

    @property
    def checkpoints_db_path(self) -> str:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return str(self.data_dir / "checkpoints.db")

    def session_db_path(self, session_id: str) -> str:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        safe = "".join(c for c in session_id if c.isalnum() or c in "-_")
        return str(self.data_dir / f"{safe}.db")


settings = Settings()
