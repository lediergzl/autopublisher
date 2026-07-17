import base64
import hashlib
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
from jose import jwt
from app.core.config import settings


def _derive_fernet_key(secret: str) -> bytes:
    # deriva una clave Fernet válida (32 bytes url-safe base64) a partir del SECRET_KEY
    digest = hashlib.sha256(secret.encode()).digest()
    return base64.urlsafe_b64encode(digest)


_fernet = Fernet(_derive_fernet_key(settings.secret_key))


def encrypt_data(data: str) -> bytes:
    return _fernet.encrypt(data.encode())


def decrypt_data(token: bytes) -> str:
    return _fernet.decrypt(token).decode()


def create_access_token(user_id: int) -> str:
    payload = {"sub": str(user_id), "exp": datetime.utcnow() + timedelta(days=7)}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except Exception:
        return None
