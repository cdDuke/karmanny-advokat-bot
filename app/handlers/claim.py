from __future__ import annotations

from contextlib import suppress

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories import ClaimRepository
from app.keyboards import BUTTON_CLAIM, MENU_BUTTONS, back_to_menu_keyboard, country_keyboard
from app.models import User
from app.services.claim import ClaimInput, ClaimService
from app.services.countries import get_country
from app.services.llm import LLMConfigurationError
from app.states import ClaimStates
from app.texts import first_start_text

router = Router(name="claim")


@router.message(F.text == BUTTON_CLAIM)
async def claim_start(message: Message, state: FSMContext, current_user: User) -> None:
    if get_country(current_user.country_code) is None:
        await state.clear()
        await message.answer(first_start_text(message.from_user.first_name or "друг"), reply_markup=country_keyboard())
        return
    await state.set_state(ClaimStates.waiting_full_name)
    await message.answer("Укажите ФИО заявителя.", reply_markup=back_to_menu_keyboard())


@router.message(ClaimStates.waiting_full_name, F.text, ~F.text.in_(MENU_BUTTONS))
async def claim_full_name(message: Message, state: FSMContext) -> None:
    await state.update_data(full_name=message.text.strip())
    await state.set_state(ClaimStates.waiting_address)
    await message.answer("Укажите адрес заявителя.")


@router.message(ClaimStates.waiting_address, F.text, ~F.text.in_(MENU_BUTTONS))
async def claim_address(message: Message, state: FSMContext) -> None:
    await state.update_data(address=message.text.strip())
    await state.set_state(ClaimStates.waiting_recipient)
    await message.answer("Кому направляется претензия? Укажите организацию, ФИО или адресата.")


@router.message(ClaimStates.waiting_recipient, F.text, ~F.text.in_(MENU_BUTTONS))
async def claim_recipient(message: Message, state: FSMContext) -> None:
    await state.update_data(recipient=message.text.strip())
    data = await state.get_data()
    if data.get("prefilled_situation"):
        await state.update_data(situation=data["prefilled_situation"])
        await state.set_state(ClaimStates.waiting_date)
        await message.answer("Контекст дела уже добавлен. Укажите дату события или нарушения.")
        return
    await state.set_state(ClaimStates.waiting_situation)
    await message.answer("Опишите ситуацию: что произошло, какие обязательства нарушены, что вы уже предпринимали.")


@router.message(ClaimStates.waiting_situation, F.text, ~F.text.in_(MENU_BUTTONS))
async def claim_situation(message: Message, state: FSMContext) -> None:
    if len(message.text.strip()) < 20:
        await message.answer("Описание слишком короткое. Добавьте детали: даты, суммы, документы, переписку.")
        return
    await state.update_data(situation=message.text.strip())
    await state.set_state(ClaimStates.waiting_date)
    await message.answer("Укажите дату события или нарушения.")


@router.message(ClaimStates.waiting_date, F.text, ~F.text.in_(MENU_BUTTONS))
async def claim_date(message: Message, state: FSMContext) -> None:
    await state.update_data(incident_date=message.text.strip())
    await state.set_state(ClaimStates.waiting_damage_amount)
    await message.answer("Укажите сумму ущерба или требований. Если суммы нет, напишите `не указана`.")


@router.message(ClaimStates.waiting_damage_amount, F.text, ~F.text.in_(MENU_BUTTONS))
async def claim_finish(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    current_user: User,
    claim_service: ClaimService,
) -> None:
    await state.update_data(damage_amount=message.text.strip())
    data = await state.get_data()

    status_message = await message.answer("Готовлю претензию и файлы...")
    claim_input = ClaimInput(
        user_id=message.from_user.id,
        full_name=data["full_name"],
        address=data["address"],
        recipient=data["recipient"],
        situation=data["situation"],
        incident_date=data["incident_date"],
        damage_amount=data["damage_amount"],
    )
    try:
        result = await claim_service.generate(claim_input, current_user.country_code or "RU")
    except LLMConfigurationError:
        await state.clear()
        with suppress(Exception):
            await status_message.delete()
        await message.answer(
            "Претензию пока нельзя сформировать: не настроен ключ LLM. "
            "Добавьте `OPENAI_API_KEY` в файл `.env`, перезапустите бота и повторите создание претензии.",
            reply_markup=back_to_menu_keyboard(),
        )
        return

    await ClaimRepository().create(
        session=session,
        user_id=message.from_user.id,
        full_name=claim_input.full_name,
        address=claim_input.address,
        recipient=claim_input.recipient,
        incident_date=claim_input.incident_date,
        damage_amount=claim_input.damage_amount,
        situation=claim_input.situation,
        document_text=result.text,
        docx_path=str(result.docx_path),
        pdf_path=str(result.pdf_path),
    )
    await state.clear()
    await status_message.delete()
    await message.answer("Претензия готова. Отправляю DOCX и PDF.", reply_markup=back_to_menu_keyboard())
    await message.answer_document(FSInputFile(result.docx_path), caption="Претензия DOCX")
    await message.answer_document(FSInputFile(result.pdf_path), caption="Претензия PDF")
