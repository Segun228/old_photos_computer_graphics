from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Iterable
from app.requests.get.get_sets import get_sets

main = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Застарить фото", callback_data="photo_start")],
        [InlineKeyboardButton(text="О разработчике", callback_data="about_dev")],
        [InlineKeyboardButton(text="Помощь", callback_data="help")],
    ]
)

back = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Домой", callback_data="main_menu")],
    ]
)
