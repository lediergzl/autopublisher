from datetime import datetime
from pydantic import BaseModel


class ActivityLogOut(BaseModel):
    id: int
    campaign_id: int | None
    community_id: int | None
    fecha: datetime
    estado: str

    class Config:
        from_attributes = True


class DashboardOut(BaseModel):
    comunidades: int
    publicaciones: int
    campanas_activas: int
    actividad_reciente: list[ActivityLogOut]
