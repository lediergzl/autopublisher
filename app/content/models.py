from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from datetime import datetime
from app.users.models import Base


class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    titulo = Column(String, nullable=False)
    contenido = Column(Text, nullable=False)  # markdown con {{variables}}
    multimedia = Column(String, nullable=True)  # URL o path de imagen/archivo
    es_plantilla = Column(Boolean, default=False)  # reutilizable en varias campañas
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
