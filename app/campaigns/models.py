import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from app.users.models import Base


class CampaignStatus(str, enum.Enum):
    draft = "draft"          # en preparación
    ready = "ready"          # lista, esperando ejecución manual
    in_progress = "in_progress"  # algunas comunidades ya publicadas
    done = "done"            # todas las comunidades seleccionadas publicadas


class PublicacionStatus(str, enum.Enum):
    pendiente = "pendiente"
    publicado = "publicado"
    error = "error"


class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    nombre = Column(String, nullable=False)
    contenido_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    estado = Column(Enum(CampaignStatus), default=CampaignStatus.draft)
    fecha_planeada = Column(DateTime, nullable=True)  # solo referencia/recordatorio
    fecha_creacion = Column(DateTime, default=datetime.utcnow)


class CampaignCommunity(Base):
    """
    Relación campaña-comunidad: cada fila es UNA comunidad objetivo de la
    campaña, y se publica solo cuando el usuario ejecuta manualmente esa fila.
    """
    __tablename__ = "campaign_communities"
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, index=True)
    community_id = Column(Integer, ForeignKey("communities.id"), nullable=False)
    publicado = Column(Enum(PublicacionStatus), default=PublicacionStatus.pendiente)
    fecha_publicacion = Column(DateTime, nullable=True)
    error_detalle = Column(String, nullable=True)
