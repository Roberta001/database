from fastapi import Header, HTTPException, status
from app.config import settings

async def verify_api_key(x_api_key: str = Header(..., description="API Secret Key for authentication")):
    if not settings.API_SECRET_KEY or x_api_key != settings.API_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key"
        )
