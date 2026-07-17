from telethon import TelegramClient
from telethon.sessions import StringSession
from app.core.security import encrypt_data, decrypt_data
from app.core.config import settings

# Telethon habla el mismo protocolo MTProto que TDLib; se usa aquí por
# simplicidad de empaquetado en Python puro (TDLib requiere binario nativo
# compilado por plataforma, lo que complica el deploy en Render).
# La cuenta conectada es siempre la del propio usuario (login manual, su número).


async def start_login(phone: str) -> tuple[str, str]:
    """
    Inicia el login: pide a Telegram que envíe el código al usuario.
    El código NUNCA se guarda; solo se usa una vez para completar el login.
    """
    client = TelegramClient(StringSession(), settings.telegram_api_id, settings.telegram_api_hash)
    await client.connect()
    sent = await client.send_code_request(phone)
    session_temporal = client.session.save()
    await client.disconnect()
    return session_temporal, sent.phone_code_hash


async def complete_login(session_temporal: str, phone: str, code: str, phone_code_hash: str) -> bytes:
    """
    Completa el login con el código que el usuario recibió en su Telegram.
    Devuelve la sesión final, cifrada, lista para guardar en DB.
    """
    client = TelegramClient(StringSession(session_temporal), settings.telegram_api_id, settings.telegram_api_hash)
    await client.connect()
    await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
    final_session = client.session.save()
    await client.disconnect()
    return encrypt_data(final_session)


async def get_client(session_encrypted: bytes) -> TelegramClient:
    """Reconstruye un cliente Telethon a partir de la sesión cifrada del usuario."""
    session_str = decrypt_data(session_encrypted)
    client = TelegramClient(StringSession(session_str), settings.telegram_api_id, settings.telegram_api_hash)
    await client.connect()
    return client
