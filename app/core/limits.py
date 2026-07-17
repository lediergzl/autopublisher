from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import HTTPException
from app.core.config import settings

# Rate limit en memoria. Para multi-worker en producción, migrar a Redis.
_calls: dict[int, list[datetime]] = defaultdict(list)


def check_limit(user_id: int, max_calls: int | None = None, window_minutes: int = 60):
    """
    Protección anti-abuso: limita cuántas publicaciones manuales puede
    ejecutar un usuario por hora, independientemente de cuántos clicks dé.
    """
    max_calls = max_calls or settings.max_posts_per_hour
    now = datetime.utcnow()
    _calls[user_id] = [t for t in _calls[user_id] if now - t < timedelta(minutes=window_minutes)]
    if len(_calls[user_id]) >= max_calls:
        raise HTTPException(429, f"Límite de {max_calls} publicaciones/hora alcanzado")
    _calls[user_id].append(now)
