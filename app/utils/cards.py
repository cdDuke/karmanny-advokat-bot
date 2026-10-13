from __future__ import annotations

from html import escape

from app.models import LegalCase


def case_number(case_id: int) -> int:
    return 2400 + case_id


def compact_title(text: str, fallback: str = "Новое дело") -> str:
    normalized = " ".join(text.replace("\n", " ").split())
    if not normalized:
        return fallback
    return normalized[:70]


def legal_case_card(item: LegalCase) -> str:
    materials = item.materials or []
    if materials:
        materials_text = "\n".join(
            f"{_material_icon(material.kind)} {escape(material.title)}" for material in materials[:6]
        )
    else:
        materials_text = "Пока нет приложенных материалов"

    return (
        f"📂 <b>Дело #{case_number(item.id)}</b>\n\n"
        f"<b>Название</b>\n{escape(item.title)}\n\n"
        f"<b>Статус</b>\n{escape(item.status)}\n\n"
        f"<b>Режим</b>\n{escape(item.mode)}\n\n"
        f"<b>Материалы</b>\n{materials_text}\n\n"
        f"<b>Последнее действие</b>\n{escape(item.last_action)}\n\n"
        "────────────────\n\n"
        "Открыть дело →"
    )


def result_card(answer: str, case_id: int, mode_label: str) -> str:
    return (
        f"📂 <b>Дело #{case_number(case_id)}</b>\n"
        f"Режим: {escape(mode_label)}\n\n"
        f"{answer}\n\n"
        "━━━━━━━━━━━━\n\n"
        "<b>Совет</b>\n\n"
        "Не отправляйте претензию без уведомления о вручении.\n\n"
        "Это увеличит ваши шансы в случае суда."
    )


def _material_icon(kind: str) -> str:
    if kind == "image":
        return "📷"
    if kind == "text":
        return "📝"
    return "📄"
