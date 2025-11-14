# handlers/callbacks.py

import asyncio
import os
import tempfile
from typing import Tuple

import yt_dlp  # не забудь добавить в requirements.txt

from maxbot.router import Router
from maxbot.dispatcher import get_current_dispatcher
from maxbot.filters import TextStartsFilter
from maxbot.types import Callback

router = Router()


# ------------------------ разбор callback_data ------------------------ #
def parse_yt_callback(data: str) -> Tuple[str, str, str]:
    """
    Ожидаемый формат callback_data / payload:
        "yt|video|itag|<url>"
        "yt|audio|itag|<url>"

    Возвращает:
        kind  - "video" или "audio"
        itag  - строка с itag формата
        url   - ссылка на видео
    """
    parts = data.split("|", 3)
    if len(parts) != 4 or parts[0] != "yt":
        raise ValueError(f"Неподдерживаемый формат callback_data: {data}")

    _, kind, itag, url = parts
    return kind, itag, url


# ------------------------ хелпер для скачивания ------------------------ #
async def download_with_yt_dlp(url: str, itag: str) -> str:
    """
    Скачивает выбранный формат в tmp-файл и возвращает путь к нему.
    """
    tmp_dir = tempfile.mkdtemp(prefix="ytbot_")
    out_tmpl = os.path.join(tmp_dir, "%(title)s.%(ext)s")

    ydl_opts = {
        "outtmpl": out_tmpl,
        "quiet": True,
        "noprogress": True,
        "format": itag,  # выбираем формат по itag
    }

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]),
    )

    files = os.listdir(tmp_dir)
    if not files:
        raise RuntimeError("Файл не был скачан")

    return os.path.join(tmp_dir, files[0])


# ------------------------ основной handler callback'ов ------------------------ #
@router.callback(TextStartsFilter("yt|"))
async def youtube_format_chosen(cb: Callback):
    """
    Обработчик нажатия на кнопку выбора качества/формата.

    cb.payload должен быть формата:
        "yt|video|itag|<url>"
        "yt|audio|itag|<url>"
    """
    bot = get_current_dispatcher().bot
    payload = cb.payload or ""

    # user_id — куда слать файл/ответы
    user_id = cb.user.id

    # 1. Парсим payload
    try:
        kind, itag, url = parse_yt_callback(payload)
    except ValueError:
        # ВМЕСТО cb.answer(...) — ответ через Bot.answer_callback
        await bot.answer_callback(
            callback_id=cb.callback_id,
            notification="Неподдерживаемый формат кнопки 😕",
        )
        return

    # 2. Подтверждаем нажатие (убираем «часики» и даём уведомление)
    await bot.answer_callback(
        callback_id=cb.callback_id,
        notification="Начал загрузку…",
    )

    # 3. Сообщаем пользователю в чат
    await bot.send_message(
        user_id=user_id,
        text="⏬ Скачиваю файл, подожди немного…",
    )

    file_path = None
    try:
        # 4. Скачиваем выбранный формат
        file_path = await download_with_yt_dlp(url, itag)

        caption = (
            "✅ Готово! Вот твоё видео."
            if kind == "video"
            else "✅ Готово! Вот твой аудио-файл."
        )
        media_type = "video" if kind == "video" else "audio"

        # 5. Отправляем файл пользователю
        await bot.send_file(
            file_path=file_path,
            media_type=media_type,
            user_id=user_id,
            text=caption,
        )

    except Exception as e:
        # Если что-то пошло не так — шлём текстом
        await bot.send_message(
            user_id=user_id,
            text=f"❌ Ошибка при загрузке: {e}",
        )
    finally:
        # 6. Чистим временный файл/папку
        if file_path:
            try:
                tmp_dir = os.path.dirname(file_path)
                try:
                    os.remove(file_path)
                except FileNotFoundError:
                    pass
                try:
                    os.rmdir(tmp_dir)
                except OSError:
                    # если вдруг ещё что-то осталось — просто забьём
                    pass
            except Exception:
                pass
