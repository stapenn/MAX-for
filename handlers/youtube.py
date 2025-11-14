from pathlib import Path
from uuid import uuid4
from typing import Dict

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils.markdown import hbold

from limits import check_limit, set_limit
from ytdl import prepare_formats, download_selected_format, human_bytes
from aiogram.types import FSInputFile


router = Router()

YOUTUBE_REGEX = r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/\S+"
DOWNLOAD_CACHE: Dict[str, str] = {}


def _build_formats_keyboard(formats, url: str, user_id: int) -> InlineKeyboardMarkup:
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
        token = uuid4().hex[:8]  # 8 символов — вообще безопасно по длине
        DOWNLOAD_CACHE[token] = url

        cb = f"yt|{token}|{fmt_id}"
        rows.append([InlineKeyboardButton(text=text, callback_data=cb)])

    return InlineKeyboardMarkup(inline_keyboard=rows)



@router.message(F.text.regexp(YOUTUBE_REGEX))
async def handle_youtube_link(message: Message):
    user_id = message.from_user.id
    url = message.text.strip()

    # 1. Проверяем лимит
    wait = check_limit(user_id)
    if wait is not None:
        await message.answer(f"Подожди ещё {wait} минут перед следующей загрузкой 🙏")
        return

    # 2. Пишем, что начали
    status_msg = await message.answer("Ищу данные о видео... 🔎")

    try:
        title, thumb, fmts = await prepare_formats(url)
    except Exception as e:
        await status_msg.edit_text("Не удалось получить информацию о видео 😥")
        return

    if not fmts:
        await status_msg.edit_text("Не нашёл подходящих форматов для скачивания.")
        return

    # 3. Ставим лимит
    set_limit(user_id)

    kb = _build_formats_keyboard(fmts, url, user_id)


    if thumb:
        # Если есть thumbnail – просто отправим текстом, без скачивания картинки
        await status_msg.edit_text(f"{hbold('Выбери формат для:')}\n{title}", reply_markup=kb)
    else:
        await status_msg.edit_text(f"{hbold('Выбери формат:')}\n{title}", reply_markup=kb)


@router.callback_query(F.data.startswith("yt|"))
async def handle_youtube_download(callback: CallbackQuery):
    await callback.answer()  # убрать "часики"

    try:
        _, token, fmt_id = callback.data.split("|", maxsplit=2)
    except Exception:
        await callback.message.answer("Некорректные данные кнопки 🤔")
        return

    # достаём url из кэша
    url = DOWNLOAD_CACHE.get(token)
    if not url:
        await callback.message.answer("Не удалось найти данные для этой кнопки, попробуй ещё раз отправить ссылку 🙏")
        return

    user_id = callback.from_user.id
    msg = await callback.message.edit_text("Скачиваю файл, подожди... ⏬")

    try:
        file_path: Path = await download_selected_format(url, fmt_id, user_id)
    except Exception as e:
        await msg.edit_text("Ошибка при скачивании видео 😢")
        # можно сразу удалить устаревший токен
        DOWNLOAD_CACHE.pop(token, None)
        return

    try:
        file = FSInputFile(path=file_path)
        await callback.message.answer_document(
            document=file,
            caption=f"Готово ✅\n{file_path.name}",
        )
        await msg.delete()
    finally:
        # чистим файл и токен
        try:
            file_path.unlink(missing_ok=True)
        except Exception:
            pass
        DOWNLOAD_CACHE.pop(token, None)
