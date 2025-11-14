# handlers/callbacks.py

import asyncio
import os
import tempfile
from typing import Tuple

from aiogram import types
from aiogram.dispatcher import Dispatcher

import yt_dlp  # не забудь добавить в requirements.txt


# ------------------------ разбор callback_data ------------------------ #
def parse_yt_callback(data: str) -> Tuple[str, str, str]:
    """
    Ожидаемый формат callback_data:
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
    # имя файла без расширения, само расширение подставит yt-dlp
    out_tmpl = os.path.join(tmp_dir, "%(title)s.%(ext)s")

    ydl_opts = {
        "outtmpl": out_tmpl,
        "quiet": True,
        "noprogress": True,
        # выбираем формат по itag
        "format": itag,
    }

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]),
    )

    # находим единственный файл в tmp_dir
    files = os.listdir(tmp_dir)
    if not files:
        raise RuntimeError("Файл не был скачан")

    return os.path.join(tmp_dir, files[0])


# ------------------------ основной handler callback'ов ------------------------ #
async def youtube_format_chosen(callback: types.CallbackQuery):
    """
    Обработчик нажатия на кнопку выбора качества/формата.

    callback.data должен быть формата:
        "yt|video|itag|<url>"
        "yt|audio|itag|<url>"
    """
    try:
        kind, itag, url = parse_yt_callback(callback.data)
    except ValueError:
        await callback.answer("Неподдерживаемый формат кнопки 😕", show_alert=True)
        return

    # уведомляем пользователя
    await callback.answer("Начал загрузку…", show_alert=False)

    msg = callback.message
    waiting = await msg.reply("⏬ Скачиваю файл, подожди немного…")

    file_path = None
    try:
        # скачиваем выбранный формат
        file_path = await download_with_yt_dlp(url, itag)

        # отправляем пользователю
        if kind == "video":
            await msg.answer_video(
                open(file_path, "rb"),
                caption="✅ Готово! Вот твоё видео.",
            )
        else:  # audio
            await msg.answer_audio(
                open(file_path, "rb"),
                caption="✅ Готово! Вот твой аудио-файл.",
            )

    except Exception as e:
        await msg.answer(f"❌ Ошибка при загрузке: {e}")
    finally:
        # чистим «Загружаю…»
        try:
            await waiting.delete()
        except Exception:
            pass

        # удаляем временный файл/папку
        if file_path:
            try:
                tmp_dir = os.path.dirname(file_path)
                # сначала удаляем файл
                try:
                    os.remove(file_path)
                except FileNotFoundError:
                    pass
                # потом директорию
                try:
                    os.rmdir(tmp_dir)
                except OSError:
                    # если там что-то ещё лежит
                    pass
            except Exception:
                pass


# ------------------------ регистрация в диспетчере ------------------------ #
def register_callback_handlers(dp: Dispatcher):
    """
    Регистрируем все callback-хендлеры этого модуля.
    Вызывай её из main.py / loader.py.
    """
    dp.register_callback_query_handler(
        youtube_format_chosen,
        lambda c: c.data and c.data.startswith("yt|"),
    )
