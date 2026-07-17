from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from app.users.models import Base


class Community(Base):
    __tablename__ = "communities"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    telegram_chat_id = Column(String, nullable=False)
    nombre = Column(String, nullable=True)
    categoria = Column(String, nullable=True, default="general")
    estado = Column(Boolean, default=True)  # activa/desactivada por el usuario
