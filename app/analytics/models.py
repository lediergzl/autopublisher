from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from app.users.models import Base


class ActivityLog(Base):
    __tablename__ = "activity_log"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    community_id = Column(Integer, ForeignKey("communities.id"), nullable=True)
    fecha = Column(DateTime, default=datetime.utcnow)
    estado = Column(String)  # "publicado" | "error"
