import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./autopublisher.db")
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-change-me")
    bot_token: str = os.getenv("BOT_TOKEN", "")
    telegram_api_id: int = int(os.getenv("TELEGRAM_API_ID", "0"))
    telegram_api_hash: str = os.getenv("TELEGRAM_API_HASH", "")
    # límite de publicaciones manuales por usuario/hora (protección anti-abuso)
    max_posts_per_hour: int = int(os.getenv("MAX_POSTS_PER_HOUR", "20"))


settings = Settings()
