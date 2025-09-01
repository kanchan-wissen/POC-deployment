from pydantic import BaseModel
from typing import Optional


class PasswordRetrieveRequest(BaseModel):
    organization_name: str
    login_url: str
    username: str


class PasswordSaveRequest(BaseModel):
    organization_name: str
    login_url: str
    username: str
    password: str


class PasswordResponse(BaseModel):
    success: bool
    password: Optional[str] = None
    message: str


class SaveResponse(BaseModel):
    success: bool
    message: str
