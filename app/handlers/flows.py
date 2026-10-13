from __future__ import annotations

import logging
from contextlib import suppress

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories import ConsultationRepository, SettingRepository, UserRepository
from app.keyboards import MENU_BUTTONS, answer_actions_keyboard, back_to_menu_keyboard, country_keyboard
from app.models import User
from app.services.consultation import ConsultationService
from app.services.countries import get_country
from app.services.llm import LLMConfigurationError
from app.states import LegalFlowStates
from app.texts import first_start_text
from app.utils.telegram import answer_long

router = Router(name="flows")
logger = logging.getLogger(__name__)


@router.message(LegalFlowStates.awaiting_draft_details, F.text, ~F.text.in_(MENU_BUTTONS))
async def draft_details(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    current_user: User,
    consultation_service: ConsultationService,
) -> None:
    country = get_country(current_user.country_code)
    if country is None:
        await state.clear()
        await message.answer(first_start_text(message.from_user.first_name or "друг"), reply_markup=country_keyboard())
        return

    text = (message.text or "").strip()
    if len(text) < 20:
        await message.answer("Добавьте чуть больше деталей: адресат, обстоятельства, цель документа и важные даты.")
        return

    data = await state.get_data()
    draft_type = data.get("draft_type", "документ")
    prompt = (
        f"Подготовь черновик юридического документа. Тип документа: {draft_type}.\n"
        f"Юрисдикция: {country.official_name}.\n\n"
        f"Данные пользователя:\n{text}\n\n"
        "Сделай официальный текст документа, затем добавь короткий блок с пояснениями: "
        "что проверить перед отправкой, какие приложения приложить и какие сроки учитывать."
    )
    await _generate_and_send(
        message=message,
        state=state,
        session=session,
        current_user=current_user,
        consultation_service=consultation_service,
        question=text,
        prompt=prompt,
        status_text="Готовлю черновик документа...",
    )


@router.message(LegalFlowStates.awaiting_risk_text, F.text, ~F.text.in_(MENU_BUTTONS))
async def risk_text(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    current_user: User,
    consultation_service: ConsultationService,
) -> None:
    country = get_country(current_user.country_code)
    if country is None:
        await state.clear()
        await message.answer(first_start_text(message.from_user.first_name or "друг"), reply_markup=country_keyboard())
        return

    text = (message.text or "").strip()
    if len(text) < 20:
        await message.answer("Опишите ситуацию подробнее: что произошло, документы, суммы, сроки и кто участвует.")
        return

    prompt = (
        f"Составь карту юридических рисков по ситуации. Юрисдикция: {country.official_name}.\n\n"
        f"Ситуация:\n{text}\n\n"
        "Ответь в формате:\n"
        "🛡️ <b>Карта рисков</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Общий уровень риска: 🟢 низкий / 🟡 средний / 🔴 высокий\n"
        "Главный риск:\n"
        "Что может произойти:\n"
        "Как снизить риск:\n"
        "Что сделать сейчас:\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    await _generate_and_send(
        message=message,
        state=state,
        session=session,
        current_user=current_user,
        consultation_service=consultation_service,
        question=text,
        prompt=prompt,
        status_text="Оцениваю риски...",
    )


@router.message(LegalFlowStates.awaiting_scenario_details, F.text, ~F.text.in_(MENU_BUTTONS))
async def scenario_details(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    current_user: User,
    consultation_service: ConsultationService,
) -> None:
    country = get_country(current_user.country_code)
    if country is None:
        await state.clear()
        await message.answer(first_start_text(message.from_user.first_name or "друг"), reply_markup=country_keyboard())
        return

    text = (message.text or "").strip()
    if len(text) < 20:
        await message.answer("Добавьте детали: даты, документы, участников и что хотите получить в итоге.")
        return

    data = await state.get_data()
    scenario_kind = data.get("scenario_kind", "Быстрый сценарий")
    scenario_detail = data.get("scenario_detail", "другое")
    prompt = (
        f"Разбери ситуацию из быстрого сценария.\n"
        f"Раздел: {scenario_kind}. Тема: {scenario_detail}.\n"
        f"Юрисдикция: {country.official_name}.\n\n"
        f"Описание пользователя:\n{text}\n\n"
        "Дай практический пошаговый ответ и укажи, какие документы пригодятся."
    )
    await _generate_and_send(
        message=message,
        state=state,
        session=session,
        current_user=current_user,
        consultation_service=consultation_service,
        question=text,
        prompt=prompt,
        status_text="Разбираю сценарий...",
    )


async def _generate_and_send(
    *,
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    current_user: User,
    consultation_service: ConsultationService,
    question: str,
    prompt: str,
    status_text: str,
) -> None:
    status_message = await message.answer(status_text)
    mode_slug = await SettingRepository().get_user_mode(session, message.from_user.id)
    try:
        answer = await consultation_service.consult(prompt, mode_slug, current_user.country_code or "RU")
    except LLMConfigurationError:
        logger.warning("Legal flow requested before OPENAI_API_KEY was configured")
        await state.clear()
        with suppress(Exception):
            await status_message.delete()
        await message.answer(
            "Сейчас не настроен ключ LLM. Добавьте <code>OPENAI_API_KEY</code> в файл <code>.env</code>, "
            "перезапустите бота и повторите запрос.",
            reply_markup=back_to_menu_keyboard(),
        )
        return

    await ConsultationRepository().create(
        session=session,
        user_id=message.from_user.id,
        question=question,
        answer=answer,
    )
    await UserRepository().increment_requests(session, current_user.id)
    await state.clear()
    with suppress(Exception):
        await status_message.delete()
    await answer_long(message, answer, reply_markup=answer_actions_keyboard())
