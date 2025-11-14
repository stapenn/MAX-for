from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "Currently bot only supports single Youtube videos (no playlists).\n"
        "Just send a Youtube url 👇"
    )
    await message.answer(text)
