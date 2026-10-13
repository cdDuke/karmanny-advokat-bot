from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Country:
    code: str
    flag: str
    name: str
    official_name: str
    law_context: str


COUNTRIES: dict[str, Country] = {
    "RU": Country(
        code="RU",
        flag="🇷🇺",
        name="Россия",
        official_name="Российская Федерация",
        law_context="законодательство Российской Федерации",
    ),
    "KZ": Country(
        code="KZ",
        flag="🇰🇿",
        name="Казахстан",
        official_name="Республика Казахстан",
        law_context="законодательство Республики Казахстан",
    ),
}


def get_country(code: str | None) -> Country | None:
    if not code:
        return None
    return COUNTRIES.get(code.upper())


def build_legal_system_prompt(country_code: str, *, document: bool = False) -> str:
    country = get_country(country_code) or COUNTRIES["RU"]
    other = "Республики Казахстан или других стран" if country.code == "RU" else "Российской Федерации или других стран"
    extra = ""
    if document:
        extra = (
            "\nДля анализа документа: определи тип документа, опасные условия, обязанности сторон, "
            "штрафы, сроки, условия расторжения, финансовые риски и рекомендации, что изменить."
        )

    return (
        "Ты — «Карманный Адвокат», юридический AI-помощник.\n"
        f"Текущая юрисдикция пользователя: {country.official_name}.\n"
        f"Отвечай только с учетом законодательства: {country.law_context}.\n"
        f"Не смешивай нормы с нормами {other}.\n"
        "Если вопрос относится к другой стране, уточни, нужно ли переключить юрисдикцию.\n"
        "Не выдумывай номера статей, законов и судебных актов. Если не уверен в точной норме, "
        "напиши, что нужно проверить актуальную редакцию.\n"
        "Давай практический, структурированный ответ на русском языке.\n"
        "Ответ носит информационный характер и не заменяет консультацию адвоката или юриста.\n"
        f"{extra}\n\n"
        "Формат ответа в HTML для Telegram:\n"
        "⚖️ <b>Юридический анализ</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🌍 Юрисдикция: {country.flag} <b>{country.name}</b>\n"
        "⚡ <b>Краткий вывод</b>\n"
        "📌 <b>Простыми словами</b>\n"
        "🛡️ <b>Риски</b>\n"
        "➡️ <b>Что сделать сейчас</b>\n"
        "📄 <b>Какие документы пригодятся</b>\n"
        "⚖️ <b>Нормы права</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Важно: ответ носит информационный характер и не заменяет консультацию юриста."
    )


def detect_foreign_country_request(text: str, current_code: str) -> str | None:
    lowered = text.lower()
    if current_code == "KZ" and any(marker in lowered for marker in ("рф", "росси", "российск")):
        return "RU"
    if current_code == "RU" and any(marker in lowered for marker in ("казахстан", "рк", "казах")):
        return "KZ"
    return None
