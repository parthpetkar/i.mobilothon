from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client
from app.database import client as supabase_client, get_user_profile
from app.redis_client import redis_client
from typing import Dict, Any

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    token = credentials.credentials
    try:
        user_response = supabase_client.auth.get_user(token)
        if not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        profile = await get_user_profile(user_response.user.id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        current_user = {
            "id": user_response.user.id,
            "email": user_response.user.email,
            "is_seller": profile.get("is_seller", False)
        }
        return current_user
    except Exception:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

async def get_current_seller(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if not current_user["is_seller"]:
        raise HTTPException(status_code=403, detail="Must be a seller")
    return current_user