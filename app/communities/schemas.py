from pydantic import BaseModel


class CommunityOut(BaseModel):
    id: int
    telegram_chat_id: str
    nombre: str | None
    categoria: str | None
    estado: bool

    class Config:
        from_attributes = True


class CommunityUpdate(BaseModel):
    categoria: str | None = None
    estado: bool | None = None
