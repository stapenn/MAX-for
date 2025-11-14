from maxbot.router import Router
from maxbot.filters import F
from maxbot.types import Message
from maxbot.dispatcher import get_current_dispatcher

router = Router()


@router.message(F.text == "/start")
async def cmd_start(message: Message):


    first_name = message.sender.first_name or ""

    text = (
        f"Привет <b>{first_name}</b>! 👋\n"
        "Используй команду /help, если хочешь узнать больше.\n\n"
        "Просто скинь ссылку на YouTube — я подберу варианты скачивания для тебя 👇"
    )

    # отправляем ответ
    await get_current_dispatcher().bot.send_message(
        chat_id=message.chat.id,   # ВАЖНО: chat_id берём именно так
        text=text,
        format="html",
        notify=True,
    )
