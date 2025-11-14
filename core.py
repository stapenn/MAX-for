# core.py
import os
import asyncio
from dotenv import load_dotenv

from maxbot.bot import Bot
from maxbot.dispatcher import Dispatcher, get_current_dispatcher
from maxbot import types

load_dotenv()
TOKEN = os.getenv("MAX_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("ENV MAX_BOT_TOKEN не задан")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ---- фильтр команд ----
class Command:
    def __init__(self, name: str):
        self.name = name.lstrip("/")

    def check(self, msg: "types.Message") -> bool:
        text = (getattr(msg, "text", "") or "").strip()
        if not text.startswith("/"):
            return False
        first = text.split()[0].lstrip("/")
        return first == self.name


# ---- утилиты отправки ----
async def send_text(chat_id, text: str, notify: bool = True):
    await get_current_dispatcher().bot.send_message(
        chat_id=chat_id,
        text=text,
        notify=notify,
    )


def _dig(obj, *path):
    """Идём по цепочке path, поддерживаем и атрибуты, и dict."""
    cur = obj
    for key in path:
        if cur is None:
            return None
        if isinstance(cur, dict):
            cur = cur.get(key)
        else:
            cur = getattr(cur, key, None)
    return cur


def extract_chat_id(msg):
    """
    Пытаемся вытащить chat_id из разных возможных форм Message.
    Под твой апдейт основная цель: recipient.chat_id.
    """
    candidates = [
        ("recipient", "chat_id"),            # msg.recipient.chat_id
        ("raw", "recipient", "chat_id"),     # msg.raw['recipient']['chat_id']
        ("message", "recipient", "chat_id"), # если вдруг внутрь завернули ещё раз
        ("peer", "chat_id"),
        ("chat", "id"),
    ]
    for path in candidates:
        val = _dig(msg, *path)
        if val is not None:
            return val

    # fallback: sender.user_id
    fallback = _dig(msg, "sender", "user_id") or _dig(
        msg, "raw", "sender", "user_id"
    )
    if fallback is not None:
        return fallback

    # отладка
    try:
        print("[extract_chat_id][DEBUG] msg.__dict__:", getattr(msg, "__dict__", None))
    except Exception:
        pass
    try:
        raw = getattr(msg, "raw", None)
        if raw is not None:
            print("[extract_chat_id][DEBUG] msg.raw keys:", list(raw.keys()))
            print("[extract_chat_id][DEBUG] msg.raw:", raw)
    except Exception:
        pass

    raise AttributeError("Не удалось извлечь chat_id")
