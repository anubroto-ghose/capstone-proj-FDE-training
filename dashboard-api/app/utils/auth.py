import os
import httpx
from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()
AUTH_BASE_URL = os.getenv("AUTH_BASE_URL", "http://127.0.0.1:8001/api/v1")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Validates token by calling the auth service /users/me endpoint
    """
    token = credentials.credentials
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{AUTH_BASE_URL}/auth/me", headers=headers)
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid token")
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail="Auth service unavailable")
