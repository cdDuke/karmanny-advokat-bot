from __future__ import annotations

from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories import HistoryRepository, UserRepository
from app.keyboards import (
    CB_COUNTRY,
    CB_MAIN_MENU,
    CB_PROFILE,
    country_keyboard,
    delete_confirm_keyboard,
    main_menu_keyboard,
    profile_keyboard,
)
from app.models import User
from app.services.countries import COUNTRIES, get_country
from app.texts import country_selected_text, first_start_text, main_menu_text, profile_text

router = Router(name="profile")


@router.message(Command("profile"))
async def profile_command(message: Message, state: FSMContext, current_user: User) -> None:
    await state.clear()
    await _send_profile(message, current_user)


@router.callback_query(F.data == CB_PROFILE)
async def profile_callback(callback: CallbackQuery, state: FSMContext, current_user: User) -> None:
    await state.clear()
    await _send_profile(callback.message, current_user)
    await callback.answer()


@router.message(Command("country"))
async def country_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "🌍 <b>Выберите юрисдикцию</b>\n\n"
        "От выбранной страны зависит, по каким законам я буду отвечать.",
        reply_markup=country_keyboard(),
    )


@router.callback_query(F.data == CB_COUNTRY)
async def country_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer(
        "🌍 <b>Выберите юрисдикцию</b>\n\n"
        "От выбранной страны зависит, по каким законам я буду отвечать.",
        reply_markup=country_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("country:"))
async def country_set_callback(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    current_user: User,
) -> None:
    await state.clear()
    country_code = callback.data.split(":", 1)[1].upper()
    country = COUNTRIES.get(country_code)
    if country is None:
        await callback.answer("Страна не найдена.", show_alert=True)
        return

    await UserRepository().set_country(session, current_user.id, country.code)
    current_user.country_code = country.code
    await callback.message.answer(country_selected_text(country), reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "profile:history")
async def profile_history_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    items = await HistoryRepository().latest_for_user(session, callback.from_user.id, limit=7)
    if not items:
        await callback.message.answer(
            "🕘 <b>История запросов</b>\n\n"
            "Пока здесь пусто.\n"
            "Когда вы начнете задавать вопросы или отправлять документы, последние обращения будут появляться здесь.",
            reply_markup=profile_keyboard(),
        )
        await callback.answer()
        return

    lines = ["🕘 <b>История запросов</b>"]
    for item in items:
        created = item.created_at.strftime("%d.%m.%Y %H:%M")
        title = escape(item.title.replace("\n", " ")[:90])
        lines.append(f"• {created} — <b>{escape(item.kind)}</b>: {title}")
    await callback.message.answer("\n".join(lines), reply_markup=profile_keyboard())
    await callback.answer()


@router.message(Command("delete_data"))
async def delete_data_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(_delete_data_prompt(), reply_markup=delete_confirm_keyboard())


@router.callback_query(F.data == "delete_data:ask")
async def delete_data_ask_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer(_delete_data_prompt(), reply_markup=delete_confirm_keyboard())
    await callback.answer()


@router.callback_query(F.data == "delete_data:confirm")
async def delete_data_confirm_callback(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    current_user: User,
) -> None:
    await state.clear()
    await UserRepository().delete_user_data(session, current_user.id)
    await callback.message.answer(
        "🗑️ <b>Данные удалены</b>\n\n"
        "Профиль, выбранная страна и локальная история запросов удалены из базы бота.\n\n"
        "Чтобы начать заново, нажмите /start.",
    )
    await callback.answer()


@router.callback_query(F.data == CB_MAIN_MENU)
async def main_menu_from_profile_callback(callback: CallbackQuery, state: FSMContext, current_user: User) -> None:
    await state.clear()
    country = get_country(current_user.country_code)
    if country is None:
        await callback.message.answer(
            first_start_text(callback.from_user.first_name or "друг"),
            reply_markup=country_keyboard(),
        )
    else:
        await callback.message.answer(main_menu_text(country), reply_markup=main_menu_keyboard())
    await callback.answer()


async def _send_profile(message: Message, current_user: User) -> None:
    country = get_country(current_user.country_code)
    await message.answer(
        profile_text(current_user.first_name or "Не указано", current_user.id, country),
        reply_markup=profile_keyboard(),
    )


def _delete_data_prompt() -> str:
    return (
        "🗑️ <b>Удалить данные?</b>\n\n"
        "Будет удален ваш профиль, выбранная страна и локальная история запросов, "
        "если она хранится в базе бота."
    )
