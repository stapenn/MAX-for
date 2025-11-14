from maxbot.router import Router
from maxbot.filters import F
from maxbot.types import Message
from maxbot.dispatcher import get_current_dispatcher

router = Router()


@router.message(F.text == "/start")
async def cmd_start(message: Message):
    """
    Для отправки ответа в umaxbot НЕЛЬЗЯ использовать message.reply()
    (такого метода нет в maxbot).

    Нужно всегда отправлять сообщение через:
    get_current_dispatcher().bot.send_message(...)
    """

    first_name = message.sender.first_name or ""

    text = (
        f"Hey <b>{first_name}</b>\n"
        "Use /help for more info\n\n"
        "Просто пришли ссылку на YouTube — я предложу варианты скачивания 👇"
    )

    # отправляем ответ
    await get_current_dispatcher().bot.send_message(
        chat_id=message.chat.id,   # ВАЖНО: chat_id берём именно так
        text=text,
        format="html",
        notify=True,
    )
