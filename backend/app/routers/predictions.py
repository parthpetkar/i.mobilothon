from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any
import httpx
from app.config import ML_SERVICE_URL

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/free-parking")
async def get_free_parking_predictions(
    lat: float = Query(..., description="User latitude"),
    lon: float = Query(..., description="User longitude"),
    radius_meters: int = Query(300, description="Search radius in meters", ge=50, le=5000)
) -> Dict[str, Any]:
    """
    Get free parking availability predictions near user location.
    
    This endpoint proxies to the ML service's prediction logic which:
    1. Fetches all data from parking_features table
    2. Filters by distance (haversine formula)
    3. Applies ML model to predict occupancy
    4. Converts to availability probability (1 - occupancy)
    5. Returns parking spots with availability predictions
    
    Query Parameters:
    - lat: User's latitude
    - lon: User's longitude
    - radius_meters: Search radius in meters (default: 300, min: 50, max: 5000)
    
    Returns:
    - parking_spots: List of nearby parking with availability predictions
    - count: Number of parking spots found
    - query: Echo of query parameters
    """
    try:
        # Call ML service
        async with httpx.AsyncClient(timeout=30.0) as client:
            ml_url = f"{ML_SERVICE_URL.rstrip('/')}/predict/free-parking"
            response = await client.get(
                ml_url,
                params={"lat": lat, "lon": lon, "radius_meters": radius_meters}
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
            "query": {"lat": lat, "lon": lon, "radius_meters": radius_meters}
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
