from telegrambot.handlers import images_events4, images_events5

import asyncio

from aiogram import Bot, Dispatcher, F

import os


async def main():
    bot = Bot(token=os.environ['telegramBotToken'])
    dp = Dispatcher()

    dp.include_routers(images_events5.router)

    await bot.delete_webhook(drop_pending_updates=True)
    print("BOT IS READY")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
