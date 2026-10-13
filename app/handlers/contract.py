from __future__ import annotations

import logging
from contextlib import suppress
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.database.repositories import CaseRepository, ContractRepository, SettingRepository, UserRepository
from app.keyboards import (
    BUTTON_CONTRACT,
    MENU_BUTTONS,
    answer_actions_keyboard,
    back_to_menu_keyboard,
    country_keyboard,
)
from app.models import User
from app.services.contract import ContractService
from app.services.countries import get_country
from app.services.llm import LLMConfigurationError
from app.services.modes import get_mode
from app.states import ContractStates
from app.texts import document_received_text, document_text, first_start_text
from app.utils.cards import compact_title
from app.utils.paths import unique_path
from app.utils.telegram import answer_long

router = Router(name="contract")
logger = logging.getLogger(__name__)


@router.message(F.text == BUTTON_CONTRACT)
async def contract_start(message: Message, state: FSMContext, current_user: User) -> None:
    country = get_country(current_user.country_code)
    if country is None:
        await state.clear()
        await message.answer(first_start_text(message.from_user.first_name or "друг"), reply_markup=country_keyboard())
        return
    await state.set_state(ContractStates.waiting_document)
    await message.answer(document_text(country), reply_markup=back_to_menu_keyboard())


@router.message(ContractStates.waiting_document, F.document | F.photo)
async def contract_file(
    message: Message,
    state: FSMContext,
    bot: Bot,
    settings: Settings,
    session: AsyncSession,
    current_user: User,
    contract_service: ContractService,
) -> None:
    country = get_country(current_user.country_code)
    if country is None:
        await state.clear()
        await message.answer(first_start_text(message.from_user.first_name or "друг"), reply_markup=country_keyboard())
        return

    file_id, file_name = _get_file_info(message)
    if file_id is None or file_name is None:
        await message.answer("Не удалось получить файл. Отправьте PDF, DOCX или изображение.")
        return

    local_path = unique_path(settings.downloads_dir, file_name)
    await bot.download(file_id, destination=local_path)

    await message.answer(document_received_text(file_name))
    state_data = await state.get_data()
    active_case_id = state_data.get("active_case_id")
    case_repo = CaseRepository()
    mode_slug = await SettingRepository().get_user_mode(session, message.from_user.id)
    mode = get_mode(mode_slug)
    try:
        result = await contract_service.analyze(
            Path(local_path),
            file_name,
            mode_slug,
            country_code=current_user.country_code or "RU",
        )
    except LLMConfigurationError:
        logger.warning("Contract analysis requested before OPENAI_API_KEY was configured")
        await state.clear()
        await message.answer(
            "Текст договора можно извлечь, но анализ через LLM пока не настроен. "
            "Добавьте <code>OPENAI_API_KEY</code> в файл <code>.env</code>, перезапустите бота и отправьте договор ещё раз.",
            reply_markup=back_to_menu_keyboard(),
        )
        return

    await ContractRepository().create(
        session=session,
        user_id=message.from_user.id,
        file_name=file_name,
        extracted_text=result.extracted_text,
        small_print=result.small_print,
        analysis=result.analysis,
        risk_level=result.risk_level,
    )
    await UserRepository().increment_documents(session, current_user.id)
    active_case = None
    if active_case_id:
        active_case = await case_repo.get_for_user(session, int(active_case_id), message.from_user.id)
    if active_case:
        legal_case = await case_repo.update_progress(
            session=session,
            item=active_case,
            context=f"{active_case.context}\n\nНовый документ: {file_name}\n\nАнализ:\n{result.analysis}",
            last_action="Добавлен документ и обновлен анализ",
            status="🟡 Проверка документа",
        )
    else:
        legal_case = await case_repo.create_case(
            session=session,
            user_id=message.from_user.id,
            title=compact_title(file_name, "Проверка документа"),
            context=f"Документ: {file_name}\n\nАнализ:\n{result.analysis}",
            last_action="Проверен документ и выделены риски",
            mode=mode.label,
            status="🟡 Проверка документа",
        )
    await case_repo.add_material(
        session=session,
        case_id=legal_case.id,
        kind="document" if message.document else "image",
        title=file_name,
        file_path=str(local_path),
    )
    await state.clear()
    await answer_long(message, result.analysis, reply_markup=answer_actions_keyboard())


@router.message(ContractStates.waiting_document, F.text, ~F.text.in_(MENU_BUTTONS))
async def contract_text(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    current_user: User,
    contract_service: ContractService,
) -> None:
    country = get_country(current_user.country_code)
    if country is None:
        await state.clear()
        await message.answer(first_start_text(message.from_user.first_name or "друг"), reply_markup=country_keyboard())
        return

    document_body = (message.text or "").strip()
    if len(document_body) < 50:
        await message.answer("Пришлите более полный текст документа или отправьте файл.", reply_markup=back_to_menu_keyboard())
        return

    await message.answer(document_received_text("Текст из сообщения"))
    state_data = await state.get_data()
    active_case_id = state_data.get("active_case_id")
    case_repo = CaseRepository()
    mode_slug = await SettingRepository().get_user_mode(session, message.from_user.id)
    mode = get_mode(mode_slug)
    try:
        result = await contract_service.analyze_text(
            document_text=document_body,
            mode=mode_slug,
            country_code=current_user.country_code or "RU",
        )
    except LLMConfigurationError:
        logger.warning("Text contract analysis requested before OPENAI_API_KEY was configured")
        await state.clear()
        await message.answer(
            "Анализ документа через LLM пока не настроен. Добавьте <code>OPENAI_API_KEY</code> в файл <code>.env</code>, "
            "перезапустите бота и отправьте документ ещё раз.",
            reply_markup=back_to_menu_keyboard(),
        )
        return

    await ContractRepository().create(
        session=session,
        user_id=message.from_user.id,
        file_name="Текст из сообщения",
        extracted_text=result.extracted_text,
        small_print=result.small_print,
        analysis=result.analysis,
        risk_level=result.risk_level,
    )
    await UserRepository().increment_documents(session, current_user.id)
    active_case = None
    if active_case_id:
        active_case = await case_repo.get_for_user(session, int(active_case_id), message.from_user.id)
    if active_case:
        legal_case = await case_repo.update_progress(
            session=session,
            item=active_case,
            context=f"{active_case.context}\n\nНовый текст документа:\n{document_body}\n\nАнализ:\n{result.analysis}",
            last_action="Добавлен текст документа и обновлен анализ",
            status="🟡 Проверка документа",
        )
    else:
        legal_case = await case_repo.create_case(
            session=session,
            user_id=message.from_user.id,
            title="Проверка текста документа",
            context=f"Текст документа:\n{document_body}\n\nАнализ:\n{result.analysis}",
            last_action="Проверен текст документа",
            mode=mode.label,
            status="🟡 Проверка документа",
        )
    await case_repo.add_material(
        session=session,
        case_id=legal_case.id,
        kind="text",
        title="Текст документа",
    )
    await state.clear()
    await answer_long(message, result.analysis, reply_markup=answer_actions_keyboard())


@router.message(ContractStates.waiting_document)
async def contract_wrong_input(message: Message) -> None:
    await message.answer("Нужен файл договора, фото или текст документа.", reply_markup=back_to_menu_keyboard())


def _get_file_info(message: Message) -> tuple[str | None, str | None]:
    if message.document:
        return message.document.file_id, message.document.file_name or "contract"
    if message.photo:
        photo = message.photo[-1]
        return photo.file_id, "contract_photo.jpg"
    return None, None
