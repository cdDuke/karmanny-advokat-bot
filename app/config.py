from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = Field(alias="BOT_TOKEN")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str | None = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.2, alias="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(default=2500, alias="OPENAI_MAX_TOKENS")

    admin_ids_raw: str = Field(default="", alias="ADMIN_IDS", repr=False)
    database_url: str = Field(default="sqlite+aiosqlite:///data/bot.db", alias="DATABASE_URL")

    tesseract_cmd: str | None = Field(default=None, alias="TESSERACT_CMD")
    tesseract_lang: str = Field(default="rus+eng", alias="TESSERACT_LANG")
    max_llm_input_chars: int = Field(default=30000, alias="MAX_LLM_INPUT_CHARS")
    small_font_pt: float = Field(default=8.0, alias="SMALL_FONT_PT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    start_preview_image: Path = Field(
        default=Path("assets/start_preview.png"),
        alias="START_PREVIEW_IMAGE",
    )
    default_country: str | None = Field(default=None, alias="DEFAULT_COUNTRY")
    enable_bot_profile_setup: bool = Field(default=True, alias="ENABLE_BOT_PROFILE_SETUP")

    data_dir: Path = Path("data")
    downloads_dir: Path = Path("data/downloads")
    generated_dir: Path = Path("data/generated")
    logs_dir: Path = Path("data/logs")
    log_file: Path = Path("data/logs/bot.log")

    @property
    def admin_ids(self) -> list[int]:
        return self.parse_admin_ids(self.admin_ids_raw)

    @staticmethod
    def parse_admin_ids(value: str | list[int] | None) -> list[int]:
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [int(item) for item in value]
        value = value.strip()
        if value.startswith("["):
            parsed = json.loads(value)
            if not isinstance(parsed, list):
                raise ValueError("ADMIN_IDS JSON value must be a list.")
            return [int(item) for item in parsed]
        return [int(item.strip()) for item in value.split(",") if item.strip()]

    @field_validator("tesseract_cmd", mode="before")
    @classmethod
    def empty_tesseract_cmd_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
