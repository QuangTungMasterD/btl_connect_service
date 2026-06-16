from fastapi import Header, HTTPException
from src.shared.config import config

async def verify_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid auth header")
    token = parts[1]
    if token != config.AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return token