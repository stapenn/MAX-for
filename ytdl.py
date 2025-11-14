import asyncio
from pathlib import Path
from typing import Any, Dict, List, Tuple

from yt_dlp import YoutubeDL

from config import DOWNLOAD_DIR


YDL_EXTRACT_OPTS = {
    "quiet": True,
    "skip_download": True,
    "no_warnings": True,
    "noplaylist": True,
}

YDL_DOWNLOAD_OPTS_BASE = {
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
}


def _build_download_opts(download_dir: Path, format_id: str | None) -> Dict[str, Any]:
    opts = YDL_DOWNLOAD_OPTS_BASE.copy()
    opts["outtmpl"] = str(download_dir / "%(title)s.%(ext)s")
    if format_id:
        opts["format"] = format_id
    return opts


async def extract_info(url: str) -> Dict[str, Any]:
    """
    Асинхронно вытягивает метаинфу о ролике.
    Возвращает dict с полями yt-dlp.
    """
    loop = asyncio.get_running_loop()

    def _extract() -> Dict[str, Any]:
        with YoutubeDL(YDL_EXTRACT_OPTS) as ydl:
            return ydl.extract_info(url, download=False)

    return await loop.run_in_executor(None, _extract)


def _filter_formats(info: Dict[str, Any]) -> List[Dict[str, Any]]:

    formats = info.get("formats", [])
    result: List[Dict[str, Any]] = []

    for f in formats:
        vcodec = f.get("vcodec")
        acodec = f.get("acodec")

        # нужно и видео, и аудио
        if vcodec == "none" or acodec == "none":
            continue

        size = f.get("filesize") or f.get("filesize_approx")
        if not size:
            continue

        result.append(f)

    # по желанию: отсортируем по размеру/качеству (не обязательно)
    result.sort(key=lambda x: (x.get("height") or 0, x.get("filesize") or 0))
    return result



def human_bytes(num: int | float) -> str:
    step_unit = 1024.0
    for x in ["B", "KB", "MB", "GB", "TB"]:
        if num < step_unit:
            return f"{num:3.1f}{x}"
        num /= step_unit
    return f"{num:.1f}PB"


async def prepare_formats(url: str) -> Tuple[str, str | None, List[Dict[str, Any]]]:
    """
    Возвращает: (title, thumbnail_url, [список форматов])
    Каждый формат: dict с полями id, ext, resolution/abr, filesize и т.д.
    """
    info = await extract_info(url)
    title = info.get("title", "No title")
    thumb = info.get("thumbnail")
    fmts = _filter_formats(info)
    return title, thumb, fmts


async def download_selected_format(url: str, format_id: str, user_id: int) -> Path:
    """
    Качает один выбранный формат.
    Возвращает путь к локальному файлу.
    """
    user_dir = DOWNLOAD_DIR / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)

    loop = asyncio.get_running_loop()

    def _download() -> Path:
        opts = _build_download_opts(user_dir, format_id)
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return Path(filename)

    return await loop.run_in_executor(None, _download)
