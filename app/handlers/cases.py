from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.database.repositories import CaseRepository
from app.documents.generator import DocumentGenerationError, LegalDocumentGenerator
from app.keyboards import (
    CB_CASES,
    back_to_menu_keyboard,
    case_actions_keyboard,
    cases_keyboard,
)
from app.states import ClaimStates, ConsultationStates, ContractStates
from app.utils.cards import case_number, legal_case_card
from app.utils.telegram import answer_long

router = Router(name="cases")


@router.callback_query(F.data == CB_CASES)
async def cases_list(callback: CallbackQuery, session: AsyncSession) -> None:
    items = await CaseRepository().latest_for_user(session, callback.from_user.id, limit=7)
    if not items:
        await callback.message.answer(
            "📂 *Мои дела*\n\nПока нет сохраненных дел. Задайте вопрос или проверьте документ — я создам дело автоматически.",
            reply_markup=back_to_menu_keyboard(),
        )
        await callback.answer()
        return

    buttons = [(item.id, f"Дело #{case_number(item.id)} · {item.title[:32]}") for item in items]
    await callback.message.answer("📂 *Мои дела*\n\nВыберите дело, чтобы вернуться к нему.", reply_markup=cases_keyboard(buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("case_open:"))
async def case_open(callback: CallbackQuery, session: AsyncSession) -> None:
    item = await _load_case(callback, session)
    if item is None:
        return
    await callback.message.answer(legal_case_card(item), reply_markup=case_actions_keyboard(item.id))
    await callback.answer()


@router.callback_query(F.data.startswith("case_pdf:"))
async def case_pdf(callback: CallbackQuery, session: AsyncSession, settings: Settings) -> None:
    item = await _load_case(callback, session)
    if item is None:
        return

    pdf_path = settings.generated_dir / f"case_{item.id}.pdf"
    try:
        LegalDocumentGenerator().generate_claim_pdf(_case_report_text(item), pdf_path)
    except DocumentGenerationError as exc:
        await callback.message.answer(str(exc), reply_markup=case_actions_keyboard(item.id))
        await callback.answer()
        return

    await callback.message.answer_document(
        FSInputFile(pdf_path),
        caption=f"📄 Дело #{case_number(item.id)}",
        reply_markup=case_actions_keyboard(item.id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("case_lawyer:"))
async def case_lawyer(callback: CallbackQuery, session: AsyncSession) -> None:
    item = await _load_case(callback, session)
    if item is None:
        return

    text = (
        "📤 *Сводка для юриста*\n\n"
        f"*Дело #{case_number(item.id)}*\n"
        f"*Название:* {item.title}\n"
        f"*Статус:* {item.status}\n"
        f"*Последнее действие:* {item.last_action}\n\n"
        f"{item.context[:2500]}\n\n"
        "Скопируйте это сообщение и отправьте выбранному юристу вместе с материалами дела."
    )
    await answer_long(callback.message, text, reply_markup=case_actions_keyboard(item.id))
    await callback.answer()


@router.callback_query(F.data.startswith("case_claim:"))
async def case_claim(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    item = await _load_case(callback, session)
    if item is None:
        return
    await state.set_state(ClaimStates.waiting_full_name)
    await state.update_data(source_case_id=item.id, prefilled_situation=item.context[:3000])
    await callback.message.answer(
        "📝 Подготовим претензию по этому делу.\n\nУкажите ФИО заявителя.",
        reply_markup=back_to_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("case_follow:"))
async def case_follow(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    item = await _load_case(callback, session)
    if item is None:
        return
    await state.set_state(ConsultationStates.waiting_question)
    await state.update_data(active_case_id=item.id)
    await callback.message.answer(
        f"🔍 *Дело #{case_number(item.id)}*\n\nЗадайте уточняющий вопрос. Я учту контекст этого дела.",
        reply_markup=back_to_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("case_adddoc:"))
async def case_add_document(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    item = await _load_case(callback, session)
    if item is None:
        return
    await state.set_state(ContractStates.waiting_document)
    await state.update_data(active_case_id=item.id)
    await callback.message.answer(
        f"➕ *Дело #{case_number(item.id)}*\n\nПришлите новый документ файлом, фотографией или текстом. Я добавлю его к делу и обновлю анализ.",
        reply_markup=back_to_menu_keyboard(),
    )
    await callback.answer()


async def _load_case(callback: CallbackQuery, session: AsyncSession):
    try:
        case_id = int(callback.data.split(":", 1)[1])
    except (AttributeError, ValueError, IndexError):
        await callback.answer("Дело не найдено.", show_alert=True)
        return None

    item = await CaseRepository().get_for_user(session, case_id, callback.from_user.id)
    if item is None:
        await callback.answer("Дело не найдено.", show_alert=True)
        return None
    return item


def _case_report_text(item) -> str:
    materials = "\n".join(f"- {material.title}" for material in item.materials) or "Материалы не приложены."
    return (
        f"Дело #{case_number(item.id)}\n\n"
        f"Название: {item.title}\n"
        f"Статус: {item.status}\n"
        f"Режим: {item.mode}\n"
        f"Последнее действие: {item.last_action}\n\n"
        f"Материалы:\n{materials}\n\n"
        f"Контекст и выводы:\n{item.context}\n\n"
        "Ответ носит информационный характер и не является официальной юридической консультацией."
    )
