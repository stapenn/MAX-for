# main.py

import asyncio
from mybot import Bot
from maxbot.dispatcher import Dispatcher
from callbacks import router as callbacks_router
from config import BOT_TOKEN
from handlers.start import router as start_router
from handlers.help import router as help_router
from handlers.youtube import router as youtube_router


async def main():
    # создаём бота
    bot = Bot(token=BOT_TOKEN)

    # создаём диспетчер
    dp = Dispatcher(bot)

    # подключаем все роутеры
    dp.include_router(start_router)
    dp.include_router(help_router)
    dp.include_router(youtube_router)
    dp.include_router(callbacks_router)

    print("🤖 Bot started...")

    # запуск polling
    await dp.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
