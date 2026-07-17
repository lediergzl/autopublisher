from pydantic import BaseModel


class LoginStartIn(BaseModel):
    phone: str


class LoginStartOut(BaseModel):
    session_temporal: str
    phone_code_hash: str


class LoginCompleteIn(BaseModel):
    session_temporal: str
    phone: str
    code: str
    phone_code_hash: str
