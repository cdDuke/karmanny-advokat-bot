from __future__ import annotations

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message

from app.utils.text import split_for_telegram


async def answer_long(message: Message, text: str, *, reply_markup=None) -> None:
    parts = split_for_telegram(text)
    for index, part in enumerate(parts):
        markup = reply_markup if index == len(parts) - 1 else None
        try:
            await message.answer(part, reply_markup=markup)
        except TelegramBadRequest:
            await message.answer(part, parse_mode=None, reply_markup=markup)
