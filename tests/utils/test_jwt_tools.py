import pytest
from authlib.jose import jwt

from app.utils.jwt_tools import issue_access_token
from app.core.config import settings


def test_issue_access_token_encodes_claims():
    token = issue_access_token("user123")
    assert isinstance(token, str)
    claims = jwt.decode(token, settings.JWT_SECRET)
    assert claims["sub"] == "user123"
    assert claims["typ"] == "access"
    assert claims["iss"] == "sangcheol-odyssey"
    assert claims["exp"] - claims["iat"] == settings.JWT_EXPIRES_SEC
    assert "aud" not in claims
