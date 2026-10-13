from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.database.repositories import UserRepository
from app.keyboards import BUTTON_HELP, about_keyboard, country_keyboard, main_menu_keyboard, privacy_keyboard
from app.models import User
from app.services.countries import COUNTRIES, get_country
from app.texts import ABOUT_TEXT, HELP_TEXT, PRIVACY_TEXT, first_start_text, main_menu_text, repeat_start_text

router = Router(name="start")


@router.message(CommandStart())
async def start_command(
    message: Message,
    state: FSMContext,
    settings: Settings,
    session: AsyncSession,
    current_user: User,
) -> None:
    await state.clear()
    if not current_user.country_code and settings.default_country in COUNTRIES:
        await UserRepository().set_country(session, current_user.id, settings.default_country or "")
        current_user.country_code = settings.default_country
    await send_start_screen(message, settings, current_user)


@router.message(Command("menu"))
async def menu_command(message: Message, state: FSMContext, current_user: User) -> None:
    await state.clear()
    country = get_country(current_user.country_code)
    if country is None:
        await message.answer(first_start_text(message.from_user.first_name or "друг"), reply_markup=country_keyboard())
        return
    await message.answer(main_menu_text(country), reply_markup=main_menu_keyboard())


@router.message(Command("help"))
@router.message(F.text == BUTTON_HELP)
async def help_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(HELP_TEXT, reply_markup=main_menu_keyboard())


@router.message(Command("about"))
async def about_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(ABOUT_TEXT, reply_markup=about_keyboard())


@router.message(Command("privacy"))
async def privacy_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(PRIVACY_TEXT, reply_markup=privacy_keyboard())


async def send_start_screen(message: Message, settings: Settings, user: User) -> None:
    country = get_country(user.country_code)
    first_name = message.chat.first_name or "друг"
    if country is None:
        text = first_start_text(first_name)
        keyboard = country_keyboard()
    else:
        text = repeat_start_text(first_name, country)
        keyboard = main_menu_keyboard()

    if settings.start_preview_image.is_file():
        await message.answer_photo(
            photo=FSInputFile(settings.start_preview_image),
            caption=text,
            reply_markup=keyboard,
        )
        return

    await message.answer(text, reply_markup=keyboard)
