from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories import HistoryRepository
from app.keyboards import BUTTON_HISTORY, back_to_menu_keyboard

router = Router(name="history")


@router.message(F.text == BUTTON_HISTORY)
async def history(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    items = await HistoryRepository().latest_for_user(session, message.from_user.id)
    if not items:
        await message.answer("История пока пустая.", reply_markup=back_to_menu_keyboard())
        return

    lines = ["*Последние запросы*"]
    for item in items:
        created = item.created_at.strftime("%d.%m.%Y %H:%M")
        title = item.title.replace("\n", " ")[:90]
        lines.append(f"• {created} — *{item.kind}*: {title}")

    await message.answer("\n".join(lines), reply_markup=back_to_menu_keyboard())
