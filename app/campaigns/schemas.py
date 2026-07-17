from datetime import datetime
from pydantic import BaseModel


class CampaignCreate(BaseModel):
    nombre: str
    contenido_id: int
    community_ids: list[int]
    fecha_planeada: datetime | None = None


class CampaignCommunityOut(BaseModel):
    id: int
    community_id: int
    publicado: str
    fecha_publicacion: datetime | None
    error_detalle: str | None

    class Config:
        from_attributes = True


class CampaignOut(BaseModel):
    id: int
    nombre: str
    contenido_id: int
    estado: str
    fecha_planeada: datetime | None
    fecha_creacion: datetime
    comunidades: list[CampaignCommunityOut] = []

    class Config:
        from_attributes = True
