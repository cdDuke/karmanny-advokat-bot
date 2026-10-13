from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.keyboards import BUTTON_FREQUENT, back_to_menu_keyboard
from app.keyboards.inline import frequent_categories_keyboard, frequent_situations_keyboard
from app.services.frequent import FREQUENT_CATEGORIES

router = Router(name="frequent")


@router.message(F.text == BUTTON_FREQUENT)
async def frequent_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Выберите категорию.", reply_markup=frequent_categories_keyboard())


@router.callback_query(F.data == "freq_back")
async def frequent_back(callback: CallbackQuery) -> None:
    await callback.message.edit_text("Выберите категорию.", reply_markup=frequent_categories_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("freq:"))
async def frequent_category(callback: CallbackQuery) -> None:
    category = callback.data.split(":", 1)[1]
    if category not in FREQUENT_CATEGORIES:
        await callback.answer("Категория не найдена.", show_alert=True)
        return
    await callback.message.edit_text(
        f"*{category}*\nВыберите ситуацию.",
        reply_markup=frequent_situations_keyboard(category),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("freq_item:"))
async def frequent_item(callback: CallbackQuery) -> None:
    _, category, raw_index = callback.data.split(":", 2)
    situations = FREQUENT_CATEGORIES.get(category)
    if not situations:
        await callback.answer("Категория не найдена.", show_alert=True)
        return
    try:
        item = situations[int(raw_index)]
    except (ValueError, IndexError):
        await callback.answer("Ситуация не найдена.", show_alert=True)
        return

    text = (
        f"*{item.title}*\n\n{item.text}\n\n"
        "Ответ носит информационный характер и не является официальной юридической консультацией."
    )
    await callback.message.answer(text, reply_markup=back_to_menu_keyboard())
    await callback.answer()
