from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any
import httpx
from app.config import ML_SERVICE_URL

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/free-parking")
async def get_free_parking_predictions(
    lat: float = Query(..., description="User latitude"),
    lon: float = Query(..., description="User longitude")
) -> Dict[str, Any]:
    """
    Get free parking availability predictions near user location.
    
    This endpoint proxies to the ML service's prediction logic which:
    1. Fetches all data from parking_features table
    2. Applies ML model to predict occupancy
    3. Converts to availability probability (1 - occupancy)
    4. Computes dynamic radius based on occupancy:
       - Low occupancy (< 0.3): 1500m radius
       - Medium occupancy (0.3-0.6): 800m radius
       - High occupancy (> 0.6): 300m radius
    5. Returns parking spots with availability predictions and dynamic radius
    
    Query Parameters:
    - lat: User's latitude
    - lon: User's longitude
    
    Returns:
    - parking_spots: List of parking with availability predictions and ML-computed radius
    - count: Number of parking spots found
    - query: Echo of query parameters
    """
    try:
        # Call ML service
        async with httpx.AsyncClient(timeout=30.0) as client:
            ml_url = f"{ML_SERVICE_URL.rstrip('/')}/free-parking/predictions"
            response = await client.get(
                ml_url,
                params={"lat": lat, "lon": lon}
            )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"ML service error: {response.text}"
            )
        
        predictions = response.json()
        return {
            "parking_spots": predictions.get("parking_spots", []),
            "count": predictions.get("count", 0),
            "query": {"lat": lat, "lon": lon}
        }
        
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to ML service: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )
