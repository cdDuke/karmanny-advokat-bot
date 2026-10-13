from __future__ import annotations

from app.prompts import CONSULTATION_PROMPT
from app.services.countries import build_legal_system_prompt
from app.services.llm import LLMService
from app.services.modes import get_mode


class ConsultationService:
    def __init__(self, llm_service: LLMService) -> None:
        self._llm = llm_service

    async def consult(self, question: str, mode: str | None = None, country_code: str = "RU") -> str:
        selected_mode = get_mode(mode)
        return await self._llm.generate(
            CONSULTATION_PROMPT.format(
                question=question.strip(),
                mode_instruction=selected_mode.instruction,
            ),
            system_prompt=build_legal_system_prompt(country_code),
        )
