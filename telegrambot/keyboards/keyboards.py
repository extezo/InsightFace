from aiogram import types
from typing import Optional, List

from pydantic import Field


def get_main_keyboard(id: int):
    buttons = [
        [
            types.InlineKeyboardButton(text="1", callback_data="main_beats"),
            types.InlineKeyboardButton(text="2", callback_data="main_service")
        ]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_upload_button(id: int):
    buttons = [
        [types.InlineKeyboardButton(text="Отправить", callback_data=f"send_backend_{id}")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_upload_btn():
    buttons = [
        [types.InlineKeyboardButton(text="Отправить", callback_data="send_backend")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def gen_select_face_keyboard(j: int, len_imgs: int, len_faces: int, is_pressed=[[]]):
    buttons = [[]]
    for i in range(len_faces):
        btntxt=str(i+1)
        if not is_pressed==[[]]:
            if is_pressed[j][i]:
                btntxt=btntxt+"*"
        buttons[0].append(
            types.InlineKeyboardButton(text=btntxt, callback_data=f'facebutton_{len_imgs}_{j}_{i}'), )

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

    return keyboard

