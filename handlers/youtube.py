# handlers/youtube.py

from pathlib import Path
from uuid import uuid4
from typing import Dict

from maxbot.router import Router
from maxbot.filters import TextStartsFilter
from maxbot.types import (
    Message,
    Callback,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from maxbot.dispatcher import get_current_dispatcher

from limits import check_limit, set_limit
from ytdl import prepare_formats, download_selected_format, human_bytes


router = Router()

YOUTUBE_DOMAINS = ("youtube.com", "youtu.be")
DOWNLOAD_CACHE: Dict[str, str] = {}


def _build_formats_keyboard(formats, url: str) -> InlineKeyboardMarkup:
    """
    На основе списка форматов собираем inline-клавиатуру.
    callback_data: yt|token|format_id
    URL храним отдельно в DOWNLOAD_CACHE[token] = url.
    """
    rows = []
    for f in formats[:15]:  # чтобы клавиатура не была бесконечной
        fmt_id = f.get("format_id")
        ext = f.get("ext", "?")
        res = f.get("resolution") or f.get("height") or ""
        abr = f.get("abr")
        size = f.get("filesize") or f.get("filesize_approx") or 0

        if res:
            quality = f"{res}"
        elif abr:
            quality = f"{abr}k audio"
        else:
            quality = "unknown"

        size_str = human_bytes(size) if size else "?"

        text = f"{ext} {quality} ({size_str})"

        # генерим короткий токен и сохраняем соответствие
        token = uuid4().hex[:8]  # 8 символов — норм
        DOWNLOAD_CACHE[token] = url

        cb = f"yt|{token}|{fmt_id}"
        rows.append([InlineKeyboardButton(text=text, callback_data=cb)])

    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message()
async def handle_youtube_link(message: Message):
    """
    Ловим все сообщения, а внутри сами фильтруем по доменам youtube.com / youtu.be.
    Никаких .reply и .recipient — только bot.send_message(user_id=...).
    """
    bot = get_current_dispatcher().bot

    text = (getattr(message, "text", "") or "").strip()
    if not text or text.startswith("/"):
        # команды и пустые сообщения игнорируем
        return

    # проверяем, что это похоже на YouTube-ссылку
    if not any(domain in text for domain in YOUTUBE_DOMAINS):
        return

    # в umaxbot/README используют message.sender.id
    user_id = message.sender.id
    url = text

    # 1. Проверяем лимит
    wait = check_limit(user_id)
    if wait is not None:
        await bot.send_message(
            user_id=user_id,
            text=f"Подожди ещё {wait} минут перед следующей загрузкой 🙏",
        )
        return

    # 2. Пишем, что начали
    await bot.send_message(
        user_id=user_id,
        text="Ищу данные о видео... 🔎",
    )

    try:
        title, thumb, fmts = await prepare_formats(url)
    except Exception:
        await bot.send_message(
            user_id=user_id,
            text="Не удалось получить информацию о видео 😥",
        )
        return

    if not fmts:
        await bot.send_message(
            user_id=user_id,
            text="Не нашёл подходящих форматов для скачивания.",
        )
        return

    # 3. Ставим лимит
    set_limit(user_id)

    kb = _build_formats_keyboard(fmts, url)
    text_resp = f"Выбери формат для:\n{title}" if thumb else f"Выбери формат:\n{title}"

    await bot.send_message(
        user_id=user_id,
        text=text_resp,
        reply_markup=kb,
    )


@router.callback(TextStartsFilter("yt|"))
async def handle_youtube_download(callback: Callback):
    """
    Обработка нажатия на inline-кнопку.
    """
    bot = get_current_dispatcher().bot

    # убрать "часики" у кнопки
    await bot.answer_callback(
        callback_id=callback.callback_id,
        notification="Начал загрузку...",  # можно текст типа "Начал загрузку…", если надо
    )

    user_id = callback.user.id

    data = callback.payload or ""
    try:
        _, token, fmt_id = data.split("|", maxsplit=2)
    except Exception:
        await bot.send_message(
            user_id=user_id,
            text="Некорректные данные кнопки 🤔",
        )
        return

    # достаём url из кэша
    url = DOWNLOAD_CACHE.get(token)
    if not url:
        await bot.send_message(
            user_id=user_id,
            text="Не удалось найти данные для этой кнопки, отправь ссылку ещё раз 🙏",
        )
        return

    await bot.send_message(
        user_id=user_id,
        text="Скачиваю файл, подожди... ⏬",
    )

    try:
        file_path: Path = await download_selected_format(url, fmt_id, user_id)
    except Exception:
        await bot.send_message(
            user_id=user_id,
            text="Ошибка при скачивании видео 😢",
        )
        DOWNLOAD_CACHE.pop(token, None)
        return

    try:
        # отправляем как универсальный файл
        await bot.send_file(
            file_path=str(file_path),
            media_type="file",
            user_id=user_id,
            text=f"Готово ✅\n{file_path.name}",
        )
    finally:
        # чистим файл и токен
        try:
            file_path.unlink(missing_ok=True)
        except Exception:
            pass
        DOWNLOAD_CACHE.pop(token, None)
