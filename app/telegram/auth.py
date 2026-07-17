import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl


def verify_init_data(init_data: str, bot_token: str, max_age_seconds: int = 86400) -> dict | None:
    """
    Valida el initData que envía Telegram Mini App según el algoritmo oficial:
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    if not init_data or not bot_token:
        return None

    parsed = dict(parse_qsl(init_data, strict_parsing=True))
    hash_recibido = parsed.pop("hash", None)
    if not hash_recibido:
        return None

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculado = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calculado, hash_recibido):
        return None

    auth_date = int(parsed.get("auth_date", 0))
    if time.time() - auth_date > max_age_seconds:
        return None  # initData expirado, evita replay attacks

    if "user" in parsed:
        parsed["user"] = json.loads(parsed["user"])

    return parsed
