import logging
import re
import zipfile
import io
from .router import user_router as router
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram import F
from typing import Dict, Any
from aiogram.fsm.context import FSMContext
from aiogram import Router, Bot
from aiogram.exceptions import TelegramAPIError
from io import BytesIO
import asyncio
from collections import defaultdict
from aiogram.types import InputFile
import aiohttp
from app.keyboards import inline_user as inline_keyboards


from aiohttp import FormData
from aiogram import Bot
from app.states.states import Set



#===========================================================================================================================
# Конфигурация основных маршрутов
#===========================================================================================================================


@router.message(CommandStart())
async def cmd_start_admin(message: Message, state: FSMContext):
    await message.reply("Приветствую! 👋")
    await message.answer("Я могу помочь вам застарить ваши фотографии")
    await message.answer("Сейчас вы можете добавлять шум, текстуры, а также добавлять эффект использования сепии")
    await message.answer("Я много что умею 👇", reply_markup=inline_keyboards.main)




@router.callback_query(F.data == "restart")
async def callback_start_admin(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    await callback.message.reply("Приветствую! 👋")
    await callback.message.answer("Я могу помочь вам застарить ваши фотографии")
    await callback.message.answer("Сейчас вы можете добавлять шум, текстуры, а также добавлять эффект использования сепии")
    await callback.message.answer("Я много что умею 👇", reply_markup=inline_keyboards.main)
    await callback.answer()


@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery):
    await callback.message.answer("Я много что умею 👇", reply_markup=inline_keyboards.main)
    await callback.answer()


@router.callback_query(F.data == "about_dev")
async def about_dev_callback(callback: CallbackQuery):
    await callback.message.answer("https://github.com/Segun228")
    await callback.message.answer("Разработал микросервисную систему студент БИВ-243 Нороха Н.", reply_markup=inline_keyboards.back)
    await callback.answer()


@router.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    await callback.message.answer("Следуйте указаниям бота")
    await callback.message.answer("Сепия - степень оттенка коричневого в фото")
    await callback.message.answer("Шум - степень зашумленности и зенистости фото", reply_markup=inline_keyboards.back)
    await callback.answer()

#===========================================================================================================================
# Основные обработчики
#===========================================================================================================================
user_photos = defaultdict(list)

@router.callback_query(F.data == "photo_start")
async def photo_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите желаемое значение шума (от 0 до 100):")
    await state.set_state(Set.noise)


@router.message(Set.noise)
async def set_noise(message: Message, state: FSMContext):
    await state.update_data(noise=int(message.text))
    await message.answer("Теперь введите уровень сепии (от 0 до 100):")
    await state.set_state(Set.sepia)


@router.message(Set.sepia)
async def set_sepia(message: Message, state: FSMContext):
    await state.update_data(sepia=int(message.text))
    await message.answer("Теперь введите уровень царапин/текстуры (от 0 до 100):")
    await state.set_state(Set.texture)


@router.message(Set.texture)
async def set_texture(message: Message, state: FSMContext):
    await state.update_data(texture=int(message.text))
    await message.answer("Теперь введите качество выходных фото (от 10 до 100):")
    await state.set_state(Set.quality)


@router.message(Set.quality)
async def set_quality(message: Message, state: FSMContext):
    await state.update_data(quality=int(message.text))
    await message.answer(
        "Отлично! Теперь скидывайте фото по одному.\nКогда закончите — напишите *готово*."
    )
    await state.set_state(Set.handle_photo)


@router.message(F.photo, Set.handle_photo)
async def save_photo(message: Message):
    file_id = message.photo[-1].file_id
    user_photos[message.from_user.id].append(file_id)
    await message.answer("Фото добавлено. Когда закончите — напишите 'готово'")

@router.message(F.text.lower() == "готово", Set.handle_photo)
async def send_photos_to_server(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    file_ids = list(dict.fromkeys(user_photos.pop(user_id, [])))  # убираем дубликаты
    if not file_ids:
        await message.answer("У вас нет загруженных фото.")
        return

    data = await state.get_data()

    form = aiohttp.FormData()
    for idx, file_id in enumerate(file_ids):
        tg_file = await bot.get_file(file_id)
        file_bytes = await bot.download_file(tg_file.file_path)
        form.add_field(
            name="files",
            value=file_bytes,
            filename=f"image_{idx}.jpg",
            content_type="image/jpeg"
        )

    form.add_field("noise", str(data.get("noise", 0)))
    form.add_field("sepia", str(data.get("sepia", 0)))
    form.add_field("scratch", str(data.get("texture", 0)))
    form.add_field("quality", str(data.get("quality", 90)))
    form.add_field("format", "jpg")

    async with aiohttp.ClientSession() as session:
        async with session.post("http://old_photos_app:8000/process_images", data=form) as response:
            if response.status != 200:
                await message.answer("Ошибка на сервере.")
                return
            zip_bytes = await response.read()

    zip_file = zipfile.ZipFile(io.BytesIO(zip_bytes))
    sent_files = set()
    for file_name in zip_file.namelist():
        if file_name in sent_files:
            continue
        sent_files.add(file_name)
        image_data = zip_file.read(file_name)
        await message.answer_photo(BufferedInputFile(image_data, filename=file_name))

    await state.clear()
    await message.answer("Ваши фото успешно застарены!", reply_markup=inline_keyboards.back)
#===========================================================================================================================
# Заглушка
#===========================================================================================================================

@router.message()
async def all_other_messages(message: Message):
    await message.answer("Неизвестная команда 🧐",reply_markup=inline_keyboards.main)


#===========================================================================================================================
# Отлов неизвестных обработчиков
#===========================================================================================================================

@router.callback_query()
async def unknown_callback(callback: CallbackQuery):
    logging.info(f"UNHANDLED CALLBACK: {callback.data}")
    await callback.answer(f"⚠️ Это действие не распознано. Получено: {callback.data}", show_alert=True)
