from maxbot.router import Router
from maxbot.filters import F
from maxbot.types import Message
from maxbot.dispatcher import get_current_dispatcher

router = Router()


@router.message(F.text == "/help")
async def cmd_help(message: Message):
    text = (
        "Currently bot only supports single Youtube videos (no playlists).\n"
        "Just send a Youtube url 👇"
    )

    await get_current_dispatcher().bot.send_message(
        chat_id=message.chat.id,
        text=text,
        notify=True
    )
