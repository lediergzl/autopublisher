from datetime import datetime
from pydantic import BaseModel


class UserOut(BaseModel):
    id: int
    telegram_id: str
    username: str | None
    fecha_creacion: datetime
    estado: str

    class Config:
        from_attributes = True
