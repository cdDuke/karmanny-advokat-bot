from __future__ import annotations

import logging

from aiogram import Router
from aiogram.types import ErrorEvent

from app.keyboards import back_to_menu_keyboard
from app.services.llm import LLMConfigurationError

router = Router(name="errors")
logger = logging.getLogger(__name__)


@router.error()
async def error_handler(event: ErrorEvent) -> bool:
    logger.exception("Unhandled update error", exc_info=event.exception)
    update = event.update
    message = update.message or update.edited_message
    callback = update.callback_query

    if isinstance(event.exception, LLMConfigurationError):
        text = (
            "Сейчас не настроен ключ LLM. Добавьте `OPENAI_API_KEY` в файл `.env`, "
            "перезапустите бота и повторите запрос."
        )
        if message:
            await message.answer(text, reply_markup=back_to_menu_keyboard())
        elif callback:
            await callback.answer("Не настроен OPENAI_API_KEY.", show_alert=True)
        return True

    if message:
        await message.answer("Произошла ошибка. Попробуйте еще раз или вернитесь в главное меню.")
    elif callback:
        await callback.answer("Произошла ошибка.", show_alert=True)
    return True
