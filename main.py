import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from handlers import start_router, help_router, youtube_router

print("BOT_TOKEN =", BOT_TOKEN[:10], "...")
async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запуск/перезапуск бота"),
        BotCommand(command="help", description="Что умеет бот"),
    ]
    await bot.set_my_commands(commands)


async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(help_router)
    dp.include_router(youtube_router)

    await set_bot_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)

    print("Bot started...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
