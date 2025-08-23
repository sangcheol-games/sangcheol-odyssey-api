from fastapi import APIRouter
from app.schemas.base_response import BaseResponse
from app.api.v1.endpoints import ping

api_router = APIRouter()
api_router.include_router(ping.router, tags=["ping"])