from fastapi import APIRouter
from app.api.v1.endpoints import (
    ping, auth_google, users, identities, auth_tokens, auth_session, auth_google_callback
)

api_router = APIRouter()
api_router.include_router(ping.router)
api_router.include_router(auth_google.router)
api_router.include_router(users.router)
api_router.include_router(identities.router)
api_router.include_router(auth_tokens.router)
api_router.include_router(auth_session.router)
api_router.include_router(auth_google_callback.router)
