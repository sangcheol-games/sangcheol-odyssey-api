from enum import StrEnum
from typing import Any, Optional

class DomainErrorCode(StrEnum):
    NICKNAME_ALREADY_SET = "NICKNAME_ALREADY_SET"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    INVALID_UID = "INVALID_UID"
    INVALID_NICKNAME = "INVALID_NICKNAME"

class SCDomainError(Exception):
    def __init__(self, code: DomainErrorCode, message: str, details: Optional[dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)
