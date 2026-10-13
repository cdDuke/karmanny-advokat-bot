from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CommunicationMode:
    slug: str
    label: str
    instruction: str


MODES: dict[str, CommunicationMode] = {
    "expert": CommunicationMode(
        slug="expert",
        label="⚖️ Эксперт",
        instruction="Отвечай как опытный юридический эксперт: строго, структурно, с акцентом на риски и доказательства.",
    ),
    "simple": CommunicationMode(
        slug="simple",
        label="💬 Простыми словами",
        instruction="Объясняй простым языком, без канцелярита, но юридически аккуратно.",
    ),
    "laws": CommunicationMode(
        slug="laws",
        label="📚 С ссылками на закон",
        instruction="Делай акцент на применимых нормах права. Не придумывай статьи, если не уверен.",
    ),
    "advocate": CommunicationMode(
        slug="advocate",
        label="🏛️ Как адвокат",
        instruction="Думай как представитель стороны: позиция защиты, аргументы, слабые места оппонента, процессуальные шаги.",
    ),
    "document": CommunicationMode(
        slug="document",
        label="📝 Подготовить документ",
        instruction="Фокусируйся на формулировках для заявлений, претензий, жалоб и официальных документов.",
    ),
}

DEFAULT_MODE = "simple"


def get_mode(slug: str | None) -> CommunicationMode:
    return MODES.get(slug or DEFAULT_MODE, MODES[DEFAULT_MODE])
