from enum import StrEnum
from typing import Any, Optional

class DomainErrorCode(StrEnum):
    NICKNAME_ALREADY_SET = "NICKNAME_ALREADY_SET"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    UID_CREATE_FAILED = "UID_CREATE_FAILED"
    INVALID_UID = "INVALID_UID"
    INVALID_NICKNAME = "INVALID_NICKNAME"
    NICKNAME_CONFLICT = "NICKNAME_CONFLICT"
    IDENTITY_CONFLICT = "IDENTITY_CONFLICT"
    PROVIDER_ALREADY_LINKED = "PROVIDER_ALREADY_LINKED"

class SCDomainError(Exception):
    def __init__(self, code: DomainErrorCode, message: str, details: Optional[dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)
