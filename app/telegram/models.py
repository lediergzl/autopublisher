from sqlalchemy import Column, Integer, LargeBinary, ForeignKey, String, DateTime
from datetime import datetime
from app.users.models import Base


class TelegramSession(Base):
    __tablename__ = "telegram_sessions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    session_encrypted = Column(LargeBinary, nullable=False)
    phone = Column(String, nullable=True)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
