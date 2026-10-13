from aiogram.fsm.state import State, StatesGroup


class ClaimStates(StatesGroup):
    waiting_full_name = State()
    waiting_address = State()
    waiting_recipient = State()
    waiting_situation = State()
    waiting_date = State()
    waiting_damage_amount = State()
