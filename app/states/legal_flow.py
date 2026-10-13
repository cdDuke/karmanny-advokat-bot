from aiogram.fsm.state import State, StatesGroup


class LegalFlowStates(StatesGroup):
    awaiting_draft_details = State()
    awaiting_risk_text = State()
    awaiting_scenario_details = State()
