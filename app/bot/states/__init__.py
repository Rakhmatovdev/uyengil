from aiogram.fsm.state import State, StatesGroup


class CreateOrder(StatesGroup):
    amount = State()
    preview = State()
