from __future__ import annotations

from openai import AsyncOpenAI

from app.config import Settings
from app.prompts import SYSTEM_PROMPT


class LLMConfigurationError(RuntimeError):
    pass


class LLMService:
    def __init__(self, settings: Settings) -> None:
        self._client: AsyncOpenAI | None = None
        if settings.openai_base_url:
            self._base_url = settings.openai_base_url
        else:
            self._base_url = None

        if settings.openai_api_key:
            client_kwargs: dict[str, str] = {"api_key": settings.openai_api_key}
            if self._base_url:
                client_kwargs["base_url"] = self._base_url
            self._client = AsyncOpenAI(**client_kwargs)

        self._model = settings.openai_model
        self._temperature = settings.openai_temperature
        self._max_tokens = settings.openai_max_tokens

    async def generate(self, prompt: str, system_prompt: str = SYSTEM_PROMPT) -> str:
        if self._client is None:
            raise LLMConfigurationError(
                "OPENAI_API_KEY не заполнен. Добавьте ключ OpenAI или совместимого API в файл .env."
            )

        response = await self._client.chat.completions.create(
            model=self._model,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("LLM вернула пустой ответ.")
        return content.strip()
