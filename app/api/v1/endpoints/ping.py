from fastapi import APIRouter
from app.schemas.base_response import BaseResponse

router = APIRouter()

@router.get("/ping", response_model=BaseResponse)
async def ping() -> BaseResponse:
    return BaseResponse(message="pong")
