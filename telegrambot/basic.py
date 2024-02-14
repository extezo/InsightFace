from telegrambot.handlers import images_events

from aiogram import Bot, Dispatcher
from aiogram.enums import ContentType
from aiogram.filters import Command
from aiogram.types import Message
import os
import asyncio
from random import randint

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram import types
from aiogram.types import FSInputFile
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
import os

from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# Вместо BOT TOKEN HERE нужно вставить токен вашего бота, полученный у @BotFather


async def main():
    bot = Bot(token=os.environ['telegramBotToken'])
    dp = Dispatcher()

    dp.include_routers(images_events.router)


    # Альтернативный вариант регистрации роутеров по одному на строку
    # dp.include_router(questions.router)
    # dp.include_router(different_types.router)

    # Запускаем бота и пропускаем все накопленные входящие
    # Да, этот метод можно вызвать даже если у вас поллинг
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())