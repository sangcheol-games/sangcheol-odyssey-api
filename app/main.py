import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.endpoints import api_router
from app.core.config import settings
from app.core.error import DomainErrorCode, SCDomainError
from app.schemas.base_response import BaseResponse

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = FastAPI(
    title="Sangcheol Odyssey API",
    description="FastAPI backend for Sangcheol Odyssey",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> BaseResponse:
    return BaseResponse(message="healthy")

@app.exception_handler(SCDomainError)
async def sc_domain_error_handler(_request: Request, exc: SCDomainError) -> JSONResponse:
    code_map = {
        DomainErrorCode.NICKNAME_ALREADY_SET: status.HTTP_400_BAD_REQUEST,
        DomainErrorCode.USER_NOT_FOUND: status.HTTP_404_NOT_FOUND,
        DomainErrorCode.INVALID_UID: status.HTTP_422_UNPROCESSABLE_ENTITY,
        DomainErrorCode.INVALID_NICKNAME: status.HTTP_422_UNPROCESSABLE_ENTITY,
    }
    status_code = code_map.get(exc.code, status.HTTP_400_BAD_REQUEST)
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message, "code": exc.code, "error_details": exc.details},
    )
