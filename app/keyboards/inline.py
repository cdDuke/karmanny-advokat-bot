from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.services.frequent import FREQUENT_CATEGORIES


def frequent_categories_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=category, callback_data=f"freq:{category}")]
        for category in FREQUENT_CATEGORIES
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def frequent_situations_keyboard(category: str) -> InlineKeyboardMarkup:
    situations = FREQUENT_CATEGORIES[category]
    buttons = [
        [InlineKeyboardButton(text=item.title, callback_data=f"freq_item:{category}:{index}")]
        for index, item in enumerate(situations)
    ]
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="freq_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Статистика", callback_data="admin:stats")],
            [InlineKeyboardButton(text="Логи ошибок", callback_data="admin:logs")],
            [InlineKeyboardButton(text="Рассылка", callback_data="admin:broadcast")],
        ]
    )
