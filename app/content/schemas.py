from datetime import datetime
from pydantic import BaseModel


class PostCreate(BaseModel):
    titulo: str
    contenido: str
    multimedia: str | None = None
    es_plantilla: bool = False


class PostUpdate(BaseModel):
    titulo: str | None = None
    contenido: str | None = None
    multimedia: str | None = None
    es_plantilla: bool | None = None


class PostOut(BaseModel):
    id: int
    titulo: str
    contenido: str
    multimedia: str | None
    es_plantilla: bool
    fecha_creacion: datetime

    class Config:
        from_attributes = True


class PostPreview(BaseModel):
    variables: dict[str, str] = {}
