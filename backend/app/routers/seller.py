from fastapi import APIRouter, Depends
from app.models import AnalyticsResponse, SellerParkingResponse
from app.database import get_analytics, get_seller_parkings
from app.dependencies import get_current_seller
from typing import List, Dict

router = APIRouter(prefix="/seller", tags=["seller"])

@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics_endpoint(current_user: Dict = Depends(get_current_seller)):
    analytics = await get_analytics(current_user["id"])
    return AnalyticsResponse(**analytics)

@router.get("/parkings", response_model=List[SellerParkingResponse])
async def get_seller_parkings_endpoint(current_user: Dict = Depends(get_current_seller)):
    parkings = await get_seller_parkings(current_user["id"])
    return [SellerParkingResponse(**p) for p in parkings]