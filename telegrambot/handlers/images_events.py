from aiogram import types
import io
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message
from telegrambot.keyboards.keyboards import get_main_keyboard, get_upload_button

router = Router()  # [1]
current_images = []
fp = io.BytesIO()
@router.message(Command("start"))  # [2]
async def go_main(message: Message):
    # user_data[message.from_user.id] = 0
    # print(message.from_user.id)
    await message.answer("Приветствую, я бот для сравнения лиц! чтобы начать пришли мне фотографию(-и)",
                         reply_markup=get_main_keyboard())


@router.message(F.photo)
async def download_photo(message: Message, bot: Bot):

    current_images.append(message.photo[-1])
    print(len(current_images))
    print(current_images)
    await bot.download(
        message.photo[-1],
        destination=f"C:/Users\myzg\Desktop/frombot/{message.photo[-1].file_id}.jpg"
    )
    print(fp.read())
    await bot.download(
        message.photo[-1],
        destination=fp
    )
    print(fp.read())

    await message.answer(
        "Нажмите отправить, когда закончите ",
        reply_markup=get_upload_button()
    )


@router.callback_query(F.data.startswith("main_"))
async def callbacks_num(callback: types.CallbackQuery):
    # user_value = user_data.get(callback.from_user.id, 0)
    # print(user_data.get(callback.from_user.id, 0))
    # action = callback.data.split("_")[1]

    # if action == "beats":
    #     # user_data[callback.from_user.id] = user_value + 1
    #     # await update_main(callback.message, 'beats')
    # elif action == "service":
    #     # user_data[callback.from_user.id] = user_value - 1
    #     # await update_main(callback.message, 'service')

    await callback.answer()
