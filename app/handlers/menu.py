from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories import SettingRepository
from app.keyboards import (
    CB_ABOUT,
    CB_CONSULT,
    CB_COUNTRY,
    CB_DRAFT,
    CB_DOCUMENT,
    CB_MAIN_MENU,
    CB_MODES,
    CB_PRIVACY,
    CB_PROFILE,
    CB_RISKS,
    CB_SCENARIOS,
    about_keyboard,
    back_to_menu_keyboard,
    country_keyboard,
    draft_type_keyboard,
    main_menu_keyboard,
    modes_keyboard,
    privacy_keyboard,
    scenario_followup_keyboard,
    scenarios_keyboard,
)
from app.models import User
from app.services.countries import get_country
from app.services.modes import MODES, get_mode
from app.states import ConsultationStates, ContractStates, LegalFlowStates
from app.texts import (
    ABOUT_TEXT,
    PRIVACY_TEXT,
    consultation_text,
    document_text,
    draft_text,
    first_start_text,
    main_menu_text,
    risks_text,
    scenarios_text,
)

router = Router(name="menu")

DRAFT_TYPES = {
    "claim": "претензия",
    "complaint": "жалоба",
    "statement": "заявление",
    "contract": "договор",
    "receipt": "расписка",
    "other": "документ",
}

SCENARIO_TITLES = {
    "work": "💼 <b>Трудовой вопрос</b>\n\nЧто произошло?",
    "realty": "🏠 <b>Недвижимость</b>\n\nЧто нужно разобрать?",
    "auto": "🚗 <b>ДТП / авто</b>\n\nОпишите, что произошло на дороге или с автомобилем.",
    "debt": "💰 <b>Долги</b>\n\nЧто нужно разобрать по долгу?",
    "consumer": "🛒 <b>Права потребителя</b>\n\nЧто произошло с товаром или услугой?",
    "family": "👨‍👩‍👧 <b>Семейный вопрос</b>\n\nЧто нужно решить?",
    "court": "🏛️ <b>Суд</b>\n\nНа какой стадии спор?",
    "contracts": "📑 <b>Договоры</b>\n\nКакой договор нужно разобрать?",
}

SCENARIO_DETAILS = {
    "salary": "не выплатили зарплату",
    "fired": "увольняют",
    "vacation": "не дают отпуск",
    "contract": "нужна проверка договора",
    "rent": "аренда",
    "sale": "покупка или продажа",
    "repair": "проблемы с ремонтом",
    "neighbors": "соседи",
    "other": "другое",
}


@router.callback_query(F.data == CB_MAIN_MENU)
async def main_menu_callback(callback: CallbackQuery, state: FSMContext, current_user: User) -> None:
    await state.clear()
    country = get_country(current_user.country_code)
    if country is None:
        await callback.message.answer(
            first_start_text(callback.from_user.first_name or "друг"),
            reply_markup=country_keyboard(),
        )
        await callback.answer()
        return
    await callback.message.answer(main_menu_text(country), reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == CB_CONSULT)
async def consult_callback(callback: CallbackQuery, state: FSMContext, current_user: User) -> None:
    country = await _require_country(callback, current_user)
    if country is None:
        return
    await state.set_state(ConsultationStates.waiting_question)
    await callback.message.answer(consultation_text(country), reply_markup=back_to_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == CB_DOCUMENT)
async def document_callback(callback: CallbackQuery, state: FSMContext, current_user: User) -> None:
    country = await _require_country(callback, current_user)
    if country is None:
        return
    await state.set_state(ContractStates.waiting_document)
    await callback.message.answer(document_text(country), reply_markup=back_to_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == CB_DRAFT)
async def draft_callback(callback: CallbackQuery, state: FSMContext, current_user: User) -> None:
    await state.clear()
    country = await _require_country(callback, current_user)
    if country is None:
        return
    await callback.message.answer(draft_text(country), reply_markup=draft_type_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("draft:"))
async def draft_type_callback(callback: CallbackQuery, state: FSMContext, current_user: User) -> None:
    country = await _require_country(callback, current_user)
    if country is None:
        return
    draft_type = callback.data.split(":", 1)[1]
    label = DRAFT_TYPES.get(draft_type, "документ")
    await state.set_state(LegalFlowStates.awaiting_draft_details)
    await state.update_data(draft_type=label)
    await callback.message.answer(
        "📝 <b>Детали документа</b>\n\n"
        f"Тип: {label}\n"
        f"Юрисдикция: {country.flag} <b>{country.name}</b>\n\n"
        "Опишите ситуацию: кому адресован документ, что произошло, чего вы хотите добиться и какие сроки важны.",
        reply_markup=back_to_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == CB_RISKS)
async def risks_callback(callback: CallbackQuery, state: FSMContext, current_user: User) -> None:
    country = await _require_country(callback, current_user)
    if country is None:
        return
    await state.set_state(LegalFlowStates.awaiting_risk_text)
    await callback.message.answer(risks_text(country), reply_markup=back_to_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == CB_SCENARIOS)
async def scenarios_callback(callback: CallbackQuery, state: FSMContext, current_user: User) -> None:
    await state.clear()
    country = await _require_country(callback, current_user)
    if country is None:
        return
    await callback.message.answer(scenarios_text(country), reply_markup=scenarios_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("scenario:"))
async def scenario_callback(callback: CallbackQuery, current_user: User) -> None:
    country = await _require_country(callback, current_user)
    if country is None:
        return
    kind = callback.data.split(":", 1)[1]
    text = SCENARIO_TITLES.get(kind, "📚 <b>Быстрый сценарий</b>\n\nЧто нужно разобрать?")
    await callback.message.answer(text, reply_markup=scenario_followup_keyboard(kind))
    await callback.answer()


@router.callback_query(F.data.startswith("scenario_detail:"))
async def scenario_detail_callback(callback: CallbackQuery, state: FSMContext, current_user: User) -> None:
    country = await _require_country(callback, current_user)
    if country is None:
        return
    _, kind, detail = callback.data.split(":", 2)
    kind_title = SCENARIO_TITLES.get(kind, "Быстрый сценарий").split("\n", 1)[0]
    detail_title = SCENARIO_DETAILS.get(detail, "другое")
    await state.set_state(LegalFlowStates.awaiting_scenario_details)
    await state.update_data(scenario_kind=kind_title, scenario_detail=detail_title)
    await callback.message.answer(
        f"{kind_title}\n\n"
        f"Тема: {detail_title}\n"
        f"Юрисдикция: {country.flag} <b>{country.name}</b>\n\n"
        "Опишите детали: что произошло, когда, кто участвует, какие документы есть и какого результата вы хотите.",
        reply_markup=back_to_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == CB_PRIVACY)
async def privacy_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer(PRIVACY_TEXT, reply_markup=privacy_keyboard())
    await callback.answer()


@router.callback_query(F.data == CB_ABOUT)
async def about_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer(ABOUT_TEXT, reply_markup=about_keyboard())
    await callback.answer()


@router.callback_query(F.data == CB_COUNTRY)
async def country_menu_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer(
        "🌍 <b>Выберите юрисдикцию</b>\n\n"
        "От выбранной страны зависит, по каким законам я буду отвечать.",
        reply_markup=country_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == CB_MODES)
async def modes_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    current = await SettingRepository().get_user_mode(session, callback.from_user.id)
    await callback.message.answer(
        "⚙️ <b>Режим общения</b>\n\nВыберите, как должен отвечать юридический помощник.",
        reply_markup=modes_keyboard(current),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("mode:"))
async def mode_set_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    slug = callback.data.split(":", 1)[1]
    if slug not in MODES:
        await callback.answer("Режим не найден.", show_alert=True)
        return
    await SettingRepository().set_user_mode(session, callback.from_user.id, slug)
    mode = get_mode(slug)
    await callback.message.answer(
        f"Готово. Теперь режим ответа: <b>{mode.label}</b>.",
        reply_markup=back_to_menu_keyboard(),
    )
    await callback.answer()


async def _require_country(callback: CallbackQuery, current_user: User):
    country = get_country(current_user.country_code)
    if country is None:
        await callback.message.answer(
            first_start_text(callback.from_user.first_name or "друг"),
            reply_markup=country_keyboard(),
        )
        await callback.answer()
        return None
    return country
