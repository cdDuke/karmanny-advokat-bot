from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

BUTTON_CONSULTATION = "Получить консультацию"
BUTTON_CONTRACT = "Проверить договор"
BUTTON_CLAIM = "Создать претензию"
BUTTON_FREQUENT = "Частые ситуации"
BUTTON_HISTORY = "История запросов"
BUTTON_HELP = "Помощь"
MENU_BUTTONS = (
    BUTTON_CONSULTATION,
    BUTTON_CONTRACT,
    BUTTON_CLAIM,
    BUTTON_FREQUENT,
    BUTTON_HISTORY,
    BUTTON_HELP,
)

CB_MAIN_MENU = "menu:main"
CB_CONSULT = "menu:consult"
CB_DOCUMENT = "menu:document"
CB_DRAFT = "menu:draft"
CB_RISKS = "menu:risks"
CB_SCENARIOS = "menu:scenarios"
CB_PROFILE = "menu:profile"
CB_COUNTRY = "menu:country"
CB_PRIVACY = "menu:privacy"
CB_ABOUT = "menu:about"
CB_CASES = "menu:cases"
CB_MODES = "menu:modes"

CB_ASK = CB_CONSULT
CB_FAQ = CB_SCENARIOS
CB_RIGHTS = CB_RISKS
CB_SITUATION = CB_CONSULT

FAQ_BUTTONS = {
    "labor": "Трудовой спор",
    "contract": "Договор",
    "fine": "Штраф",
    "debt": "Долг",
    "rent": "Аренда",
    "family": "Семейный вопрос",
}


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⚖️ Консультация", callback_data=CB_CONSULT),
                InlineKeyboardButton(text="📄 Проверить документ", callback_data=CB_DOCUMENT),
            ],
            [
                InlineKeyboardButton(text="📝 Составить документ", callback_data=CB_DRAFT),
                InlineKeyboardButton(text="🛡️ Найти риски", callback_data=CB_RISKS),
            ],
            [
                InlineKeyboardButton(text="📚 Быстрые сценарии", callback_data=CB_SCENARIOS),
                InlineKeyboardButton(text="👤 Профиль", callback_data=CB_PROFILE),
            ],
            [
                InlineKeyboardButton(text="🌍 Сменить страну", callback_data=CB_COUNTRY),
                InlineKeyboardButton(text="ℹ️ О боте", callback_data=CB_ABOUT),
            ],
            [
                InlineKeyboardButton(text="🔒 Конфиденциальность", callback_data=CB_PRIVACY),
            ],
        ],
    )


def country_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇷🇺 Россия — законы РФ", callback_data="country:RU")],
            [InlineKeyboardButton(text="🇰🇿 Казахстан — законы РК", callback_data="country:KZ")],
        ]
    )


def switch_country_keyboard(current_code: str, other_code: str) -> InlineKeyboardMarkup:
    current_text = "🇷🇺 Оставить Россию" if current_code == "RU" else "🇰🇿 Оставить Казахстан"
    other_text = "🇷🇺 Переключить на Россию" if other_code == "RU" else "🇰🇿 Переключить на Казахстан"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=current_text, callback_data=f"jurisdiction_keep:{current_code}")],
            [InlineKeyboardButton(text=other_text, callback_data=f"jurisdiction_switch:{other_code}")],
        ]
    )


def profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌍 Сменить страну", callback_data=CB_COUNTRY)],
            [InlineKeyboardButton(text="🕘 История запросов", callback_data="profile:history")],
            [InlineKeyboardButton(text="🔒 Конфиденциальность", callback_data=CB_PRIVACY)],
            [InlineKeyboardButton(text="⬅️ Главное меню", callback_data=CB_MAIN_MENU)],
        ]
    )


def privacy_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑️ Удалить мои данные", callback_data="delete_data:ask")],
            [InlineKeyboardButton(text="⬅️ Главное меню", callback_data=CB_MAIN_MENU)],
        ]
    )


def about_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌍 Сменить страну", callback_data=CB_COUNTRY)],
            [InlineKeyboardButton(text="⬅️ Главное меню", callback_data=CB_MAIN_MENU)],
        ]
    )


def delete_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, удалить", callback_data="delete_data:confirm")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data=CB_MAIN_MENU)],
        ]
    )


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Главное меню", callback_data=CB_MAIN_MENU)],
        ]
    )


def draft_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Претензия", callback_data="draft:claim"),
                InlineKeyboardButton(text="🏛️ Жалоба", callback_data="draft:complaint"),
            ],
            [
                InlineKeyboardButton(text="📄 Заявление", callback_data="draft:statement"),
                InlineKeyboardButton(text="🤝 Договор", callback_data="draft:contract"),
            ],
            [
                InlineKeyboardButton(text="💰 Расписка", callback_data="draft:receipt"),
                InlineKeyboardButton(text="✍️ Другое", callback_data="draft:other"),
            ],
            [InlineKeyboardButton(text="⬅️ Главное меню", callback_data=CB_MAIN_MENU)],
        ]
    )


def scenarios_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [("💼 Работа", "scenario:work"), ("🏠 Недвижимость", "scenario:realty")],
        [("🚗 ДТП / авто", "scenario:auto"), ("💰 Долги", "scenario:debt")],
        [("🛒 Права потребителя", "scenario:consumer"), ("👨‍👩‍👧 Семья", "scenario:family")],
        [("🏛️ Суд", "scenario:court"), ("📑 Договоры", "scenario:contracts")],
    ]
    buttons = [[InlineKeyboardButton(text=text, callback_data=data) for text, data in row] for row in rows]
    buttons.append([InlineKeyboardButton(text="⬅️ Главное меню", callback_data=CB_MAIN_MENU)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def scenario_followup_keyboard(kind: str) -> InlineKeyboardMarkup:
    if kind == "work":
        rows = [
            [("💸 Не выплатили зарплату", "scenario_detail:work:salary")],
            [("🚪 Увольняют", "scenario_detail:work:fired")],
            [("📅 Не дают отпуск", "scenario_detail:work:vacation")],
            [("📄 Нужна проверка договора", "scenario_detail:work:contract")],
            [("✍️ Другое", "scenario_detail:work:other")],
        ]
    elif kind == "realty":
        rows = [
            [("🏘️ Аренда", "scenario_detail:realty:rent")],
            [("🏡 Покупка / продажа", "scenario_detail:realty:sale")],
            [("🔧 Проблемы с ремонтом", "scenario_detail:realty:repair")],
            [("📄 Договор", "scenario_detail:realty:contract")],
            [("👥 Соседи", "scenario_detail:realty:neighbors")],
            [("✍️ Другое", "scenario_detail:realty:other")],
        ]
    else:
        rows = [[("✍️ Описать ситуацию", f"scenario_detail:{kind}:other")]]
    buttons = [[InlineKeyboardButton(text=text, callback_data=data)] for row in rows for text, data in row]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=CB_SCENARIOS)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def modes_keyboard(selected: str = "simple") -> InlineKeyboardMarkup:
    labels = {
        "expert": "⚖️ Эксперт",
        "simple": "💬 Простыми словами",
        "laws": "📚 С ссылками на закон",
        "advocate": "🏛️ Как адвокат",
        "document": "📝 Подготовить документ",
    }
    buttons = []
    for slug, label in labels.items():
        prefix = "✓ " if slug == selected else ""
        buttons.append([InlineKeyboardButton(text=f"{prefix}{label}", callback_data=f"mode:{slug}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Главное меню", callback_data=CB_MAIN_MENU)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def answer_actions_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Составить документ", callback_data=CB_DRAFT)],
            [InlineKeyboardButton(text="🔍 Задать уточнение", callback_data=CB_CONSULT)],
            [InlineKeyboardButton(text="⬅️ Главное меню", callback_data=CB_MAIN_MENU)],
        ]
    )


def case_actions_keyboard(case_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📄 Скачать PDF", callback_data=f"case_pdf:{case_id}"),
                InlineKeyboardButton(text="📤 Отправить юристу", callback_data=f"case_lawyer:{case_id}"),
            ],
            [InlineKeyboardButton(text="📝 Подготовить претензию", callback_data=f"case_claim:{case_id}")],
            [InlineKeyboardButton(text="➕ Добавить документ", callback_data=f"case_adddoc:{case_id}")],
            [InlineKeyboardButton(text="🔍 Задать уточняющий вопрос", callback_data=f"case_follow:{case_id}")],
            [InlineKeyboardButton(text="⬅️ Главное меню", callback_data=CB_MAIN_MENU)],
        ]
    )


def case_open_keyboard(case_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть дело →", callback_data=f"case_open:{case_id}")],
            [InlineKeyboardButton(text="⬅️ Главное меню", callback_data=CB_MAIN_MENU)],
        ]
    )


def cases_keyboard(case_ids: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text=title, callback_data=f"case_open:{case_id}")] for case_id, title in case_ids]
    buttons.append([InlineKeyboardButton(text="⬅️ Главное меню", callback_data=CB_MAIN_MENU)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def faq_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=title, callback_data=f"faq:{slug}")]
        for slug, title in FAQ_BUTTONS.items()
    ]
    buttons.append([InlineKeyboardButton(text="⬅️ Главное меню", callback_data=CB_MAIN_MENU)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
