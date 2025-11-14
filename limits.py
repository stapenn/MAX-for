from datetime import datetime, timedelta
from typing import Dict

from config import YOUTUBE_NEXT_FETCH_MINUTES

# user_id -> datetime, когда можно снова качать
_user_next_time: Dict[int, datetime] = {}


def check_limit(user_id: int) -> float | None:
    """
    Проверяет, можно ли пользователю качать сейчас.
    Возвращает None, если можно.
    Возвращает кол-во минут ожидания (float), если нельзя.
    """
    now = datetime.utcnow()
    next_time = _user_next_time.get(user_id)
    if next_time and next_time > now:
        delta = next_time - now
        return round(delta.total_seconds() / 60, 2)
    return None


def set_limit(user_id: int) -> None:
    now = datetime.utcnow()
    _user_next_time[user_id] = now + timedelta(minutes=YOUTUBE_NEXT_FETCH_MINUTES)
