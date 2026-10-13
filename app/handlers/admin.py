from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.database.repositories import StatsRepository, UserRepository
from app.keyboards import back_to_menu_keyboard
from app.keyboards.inline import admin_keyboard
from app.states import AdminBroadcastStates

router = Router(name="admin")
logger = logging.getLogger(__name__)


def _is_admin(user_id: int, settings: Settings) -> bool:
    return user_id in set(settings.admin_ids)


@router.message(Command("admin"))
async def admin_panel(message: Message, settings: Settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        await message.answer("Админ-панель недоступна.")
        return
    await message.answer("*Админ-панель*", reply_markup=admin_keyboard())


@router.callback_query(F.data == "admin:stats")
async def admin_stats(callback: CallbackQuery, settings: Settings, session: AsyncSession) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer("Недоступно.", show_alert=True)
        return
    counts = await StatsRepository().counts(session)
    text = (
        "*Статистика*\n\n"
        f"Пользователей: {counts['users']}\n"
        f"Консультаций: {counts['consultations']}\n"
        f"Проверенных договоров: {counts['contracts']}\n"
        f"Созданных претензий: {counts['claims']}\n"
        f"Юридических дел: {counts['cases']}"
    )
    await callback.message.edit_text(text, reply_markup=admin_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:logs")
async def admin_logs(callback: CallbackQuery, settings: Settings) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer("Недоступно.", show_alert=True)
        return
    log_text = _read_recent_errors(settings)
    await callback.message.answer(log_text, parse_mode=None)
    await callback.answer()


@router.callback_query(F.data == "admin:broadcast")
async def admin_broadcast_start(callback: CallbackQuery, settings: Settings, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer("Недоступно.", show_alert=True)
        return
    await state.set_state(AdminBroadcastStates.waiting_text)
    await callback.message.answer("Введите текст рассылки.")
    await callback.answer()


@router.message(AdminBroadcastStates.waiting_text, F.text)
async def admin_broadcast_send(
    message: Message,
    state: FSMContext,
    settings: Settings,
    session: AsyncSession,
    bot: Bot,
) -> None:
    if not _is_admin(message.from_user.id, settings):
        await state.clear()
        await message.answer("Недоступно.", reply_markup=back_to_menu_keyboard())
        return

    user_ids = await UserRepository().all_user_ids(session)
    sent = 0
    failed = 0
    for user_id in user_ids:
        try:
            await bot.send_message(user_id, message.text, parse_mode=None)
            sent += 1
        except Exception as exc:
            failed += 1
            logger.warning("Broadcast to user %s failed: %s", user_id, exc)

    await state.clear()
    await message.answer(f"Рассылка завершена. Доставлено: {sent}. Ошибок: {failed}.", reply_markup=admin_keyboard())


def _read_recent_errors(settings: Settings, max_lines: int = 40) -> str:
    if not settings.log_file.exists():
        return "Лог-файл пока пуст."
    lines = settings.log_file.read_text(encoding="utf-8", errors="ignore").splitlines()
    errors = [line for line in lines if "ERROR" in line or "CRITICAL" in line]
    if not errors:
        return "Ошибок в логах не найдено."
    return "Последние ошибки\n\n" + "\n".join(errors[-max_lines:])[-3500:]
