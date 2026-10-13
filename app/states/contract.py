from aiogram.fsm.state import State, StatesGroup


class ContractStates(StatesGroup):
    waiting_document = State()
