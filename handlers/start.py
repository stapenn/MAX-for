from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):

    text = f"Hey <b>{message.from_user.first_name}</b>\nUse /help for more info"
    await message.answer(text)
