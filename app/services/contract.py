from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.config import Settings
from app.ocr.extractors import DocumentTextExtractor
from app.prompts import CONTRACT_PROMPT
from app.services.countries import build_legal_system_prompt
from app.services.llm import LLMService
from app.services.modes import get_mode
from app.utils.text import clamp_text


@dataclass(slots=True)
class ContractAnalysisResult:
    extracted_text: str
    small_print: str | None
    analysis: str
    risk_level: str


class ContractService:
    def __init__(
        self,
        settings: Settings,
        extractor: DocumentTextExtractor,
        llm_service: LLMService,
    ) -> None:
        self._settings = settings
        self._extractor = extractor
        self._llm = llm_service

    async def analyze(
        self,
        file_path: Path,
        file_name: str,
        mode: str | None = None,
        country_code: str = "RU",
    ) -> ContractAnalysisResult:
        extracted = await self._extractor.extract(file_path, file_name)
        return await self.analyze_text(
            document_text=extracted.text,
            file_name=file_name,
            small_print=extracted.small_print,
            mode=mode,
            country_code=country_code,
        )

    async def analyze_text(
        self,
        document_text: str,
        file_name: str = "text_message",
        small_print: str | None = None,
        mode: str | None = None,
        country_code: str = "RU",
    ) -> ContractAnalysisResult:
        raw_text = document_text.strip()
        document_text_for_prompt = clamp_text(raw_text, self._settings.max_llm_input_chars)
        small_print_for_prompt = clamp_text(small_print or "Не обнаружен или не распознан.", 5000)
        selected_mode = get_mode(mode)

        analysis = await self._llm.generate(
            CONTRACT_PROMPT.format(
                document_text=document_text_for_prompt,
                small_print=small_print_for_prompt,
                mode_instruction=selected_mode.instruction,
            ),
            system_prompt=build_legal_system_prompt(country_code, document=True),
        )
        # Машинный уровень риска нужен для статистики и будущей фильтрации истории.
        return ContractAnalysisResult(
            extracted_text=raw_text,
            small_print=small_print,
            analysis=analysis,
            risk_level=self._extract_risk_level(analysis),
        )

    @staticmethod
    def _extract_risk_level(analysis: str) -> str:
        lowered = analysis.lower()
        if "🔴" in analysis or "высокий риск" in lowered:
            return "high"
        if "🟡" in analysis or "требует внимания" in lowered:
            return "medium"
        if "🟢" in analysis or "безопасный" in lowered:
            return "low"
        return "unknown"
