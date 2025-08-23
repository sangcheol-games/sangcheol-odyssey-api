from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, HttpUrl

class GoogleAuthParams(BaseModel):
    client_id: str
    redirect_uri: str
    response_type: Literal["code"] = "code"
    scope: str = "openid email profile"
    code_challenge: str
    code_challenge_method: Literal["S256"] = "S256"
    state: str
    nonce: str
    access_type: Literal["online", "offline"] = "offline"
    prompt: Literal["none", "consent", "select_account"] | None = None

class GoogleTokenRequest(BaseModel):
    client_id: str
    code: str
    redirect_uri: str
    grant_type: Literal["authorization_code"] = "authorization_code"
    code_verifier: str
    client_secret: str | None = None

    def to_form(self) -> dict[str, str]:
        return {k: str(v) for k, v in self.model_dump(exclude_none=True).items()}

class GoogleTokenResponse(BaseModel):
    access_token: str | None = None
    expires_in: int | None = None
    token_type: str | None = None
    id_token: str | None = None
    refresh_token: str | None = None
    scope: str | None = None

class GoogleIdClaims(BaseModel):
    iss: str | None = None
    aud: str | None = None
    sub: str | None = None
    iat: int | None = None
    exp: int | None = None
    email: str | None = None
    email_verified: bool | None = None
    name: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    picture: HttpUrl | None = None
    locale: str | None = None
    nonce: str | None = None
