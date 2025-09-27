from aiogram.fsm.state import StatesGroup, State


class Set(StatesGroup):
    handle_photo = State()
    noise = State()
    sepia = State()
    texture = State()
    quality = State()
