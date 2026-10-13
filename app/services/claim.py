from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from app.config import Settings
from app.documents.generator import LegalDocumentGenerator
from app.prompts import CLAIM_PROMPT
from app.services.countries import build_legal_system_prompt, get_country
from app.services.llm import LLMService
from app.templates import CLAIM_FILE_PREFIX


@dataclass(slots=True)
class ClaimInput:
    user_id: int
    full_name: str
    address: str
    recipient: str
    situation: str
    incident_date: str
    damage_amount: str


@dataclass(slots=True)
class ClaimResult:
    text: str
    docx_path: Path
    pdf_path: Path


class ClaimService:
    def __init__(self, settings: Settings, llm_service: LLMService) -> None:
        self._settings = settings
        self._llm = llm_service
        self._generator = LegalDocumentGenerator()

    async def generate(self, data: ClaimInput, country_code: str = "RU") -> ClaimResult:
        country = get_country(country_code)
        text = await self._llm.generate(
            CLAIM_PROMPT.format(
                country_name=country.official_name if country else "выбранная страна",
                full_name=data.full_name,
                address=data.address,
                recipient=data.recipient,
                situation=data.situation,
                incident_date=data.incident_date,
                damage_amount=data.damage_amount,
            ),
            system_prompt=build_legal_system_prompt(country_code),
        )
        base_name = f"{CLAIM_FILE_PREFIX}_{data.user_id}_{uuid4().hex[:12]}"
        docx_path = self._settings.generated_dir / f"{base_name}.docx"
        pdf_path = self._settings.generated_dir / f"{base_name}.pdf"

        self._generator.generate_claim_docx(text, docx_path)
        self._generator.generate_claim_pdf(text, pdf_path)
        return ClaimResult(text=text, docx_path=docx_path, pdf_path=pdf_path)
