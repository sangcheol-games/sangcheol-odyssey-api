from __future__ import annotations
from typing import Literal
from pydantic import BaseModel

class ExchangeRequest(BaseModel):
    code: str
    code_verifier: str

class VerifyIdTokenRequest(BaseModel):
    id_token: str

class AuthUrlResponse(BaseModel):
    auth_url: str
    session_id: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    refresh_token: str | None = None
    expires_in: int
    is_new_user: bool
