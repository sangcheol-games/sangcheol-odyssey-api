from pydantic import BaseModel

class SteamLoginRequest(BaseModel):
    ticket: str
