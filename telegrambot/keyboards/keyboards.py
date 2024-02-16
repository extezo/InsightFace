
from aiogram import types

def get_main_keyboard():
    buttons = [
        [
            types.InlineKeyboardButton(text="1", callback_data="main_beats"),
            types.InlineKeyboardButton(text="2", callback_data="main_service")
        ]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard



def get_upload_button():
    buttons = [
        [types.InlineKeyboardButton(text="Отправить", callback_data="send_backend")],
        ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard