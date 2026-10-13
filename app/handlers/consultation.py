from __future__ import annotations

import logging
from contextlib import suppress

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories import CaseRepository, ConsultationRepository, SettingRepository, UserRepository
from app.keyboards import (
    BUTTON_CONSULTATION,
    MENU_BUTTONS,
    answer_actions_keyboard,
    back_to_menu_keyboard,
    country_keyboard,
    switch_country_keyboard,
)
from app.models import User
from app.services.consultation import ConsultationService
from app.services.countries import detect_foreign_country_request, get_country
from app.services.llm import LLMConfigurationError
from app.services.modes import get_mode
from app.states import ConsultationStates
from app.texts import consultation_text, first_start_text
from app.utils.cards import compact_title
from app.utils.telegram import answer_long

router = Router(name="consultation")
logger = logging.getLogger(__name__)


@router.message(F.text == BUTTON_CONSULTATION)
async def consultation_start(message: Message, state: FSMContext, current_user: User) -> None:
    country = get_country(current_user.country_code)
    if country is None:
        await state.clear()
        await message.answer(first_start_text(message.from_user.first_name or "друг"), reply_markup=country_keyboard())
        return
    await state.set_state(ConsultationStates.waiting_question)
    await message.answer(consultation_text(country), reply_markup=back_to_menu_keyboard())


@router.message(ConsultationStates.waiting_question, F.text, ~F.text.in_(MENU_BUTTONS))
async def consultation_question(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    current_user: User,
    consultation_service: ConsultationService,
) -> None:
    question = (message.text or "").strip()
    if len(question) < 10:
        await message.answer("Опишите ситуацию чуть подробнее: что произошло, когда и с кем.")
        return

    country = get_country(current_user.country_code)
    if country is None:
        await state.clear()
        await message.answer(first_start_text(message.from_user.first_name or "друг"), reply_markup=country_keyboard())
        return

    other_code = detect_foreign_country_request(question, country.code)
    if other_code:
        other = get_country(other_code)
        await state.update_data(pending_question=question)
        await message.answer(
            f"Вы сейчас выбрали юрисдикцию: {country.flag} <b>{country.name}</b>.\n"
            f"Разобрать вопрос по законам {country.official_name} или переключиться на {other.name}?",
            reply_markup=switch_country_keyboard(country.code, other.code),
        )
        return

    await _process_question(
        target=message,
        state=state,
        session=session,
        current_user=current_user,
        telegram_user_id=message.from_user.id,
        consultation_service=consultation_service,
        question=question,
    )


@router.callback_query(F.data.startswith("jurisdiction_keep:"))
async def jurisdiction_keep_callback(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    current_user: User,
    consultation_service: ConsultationService,
) -> None:
    data = await state.get_data()
    question = data.get("pending_question")
    if not question:
        await callback.message.answer("Напишите юридический вопрос одним сообщением.", reply_markup=back_to_menu_keyboard())
        await callback.answer()
        return

    await callback.answer()
    await _process_question(
        target=callback.message,
        state=state,
        session=session,
        current_user=current_user,
        telegram_user_id=callback.from_user.id,
        consultation_service=consultation_service,
        question=question,
    )


@router.callback_query(F.data.startswith("jurisdiction_switch:"))
async def jurisdiction_switch_callback(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    current_user: User,
    consultation_service: ConsultationService,
) -> None:
    new_code = callback.data.split(":", 1)[1].upper()
    country = get_country(new_code)
    if country is None:
        await callback.answer("Страна не найдена.", show_alert=True)
        return

    await UserRepository().set_country(session, current_user.id, country.code)
    current_user.country_code = country.code
    data = await state.get_data()
    question = data.get("pending_question")
    await callback.message.answer(
        f"✅ Юрисдикция переключена: {country.flag} <b>{country.name}</b>.\n\n"
        "Сейчас разберу вопрос с учетом выбранной страны."
    )
    await callback.answer()
    if not question:
        await callback.message.answer("Напишите юридический вопрос одним сообщением.", reply_markup=back_to_menu_keyboard())
        return

    await _process_question(
        target=callback.message,
        state=state,
        session=session,
        current_user=current_user,
        telegram_user_id=callback.from_user.id,
        consultation_service=consultation_service,
        question=question,
    )


async def _process_question(
    *,
    target: Message,
    state: FSMContext,
    session: AsyncSession,
    current_user: User,
    telegram_user_id: int,
    consultation_service: ConsultationService,
    question: str,
) -> None:
    state_data = await state.get_data()
    active_case_id = state_data.get("active_case_id")
    setting_repo = SettingRepository()
    case_repo = CaseRepository()
    mode_slug = await setting_repo.get_user_mode(session, telegram_user_id)
    mode = get_mode(mode_slug)
    prompt_question = question
    active_case = None
    if active_case_id:
        active_case = await case_repo.get_for_user(session, int(active_case_id), telegram_user_id)
        if active_case:
            prompt_question = (
                f"Контекст предыдущего дела:\n{active_case.context}\n\n"
                f"Уточняющий вопрос пользователя:\n{question}"
            )

    status_message = await target.answer("Анализирую ситуацию...")
    try:
        answer = await consultation_service.consult(prompt_question, mode_slug, current_user.country_code or "RU")
    except LLMConfigurationError:
        logger.warning("Consultation requested before OPENAI_API_KEY was configured")
        await state.clear()
        with suppress(Exception):
            await status_message.delete()
        await target.answer(
            "Сейчас не настроен ключ LLM. Добавьте <code>OPENAI_API_KEY</code> в файл <code>.env</code>, "
            "перезапустите бота и повторите запрос.",
            reply_markup=back_to_menu_keyboard(),
        )
        return

    await ConsultationRepository().create(
        session=session,
        user_id=telegram_user_id,
        question=question,
        answer=answer,
    )
    await UserRepository().increment_requests(session, current_user.id)
    if active_case:
        await case_repo.update_progress(
            session=session,
            item=active_case,
            context=f"{active_case.context}\n\nУточнение пользователя:\n{question}\n\nОтвет:\n{answer}",
            last_action="Обновлен план защиты",
        )
    else:
        legal_case = await case_repo.create_case(
            session=session,
            user_id=telegram_user_id,
            title=compact_title(question, "Юридическая консультация"),
            context=f"Вопрос:\n{question}\n\nОтвет:\n{answer}",
            last_action="Подготовлен план защиты",
            mode=mode.label,
        )
        await case_repo.add_material(
            session=session,
            case_id=legal_case.id,
            kind="text",
            title="Описание ситуации",
        )
    await state.clear()
    with suppress(Exception):
        await status_message.delete()
    await answer_long(target, answer, reply_markup=answer_actions_keyboard())
