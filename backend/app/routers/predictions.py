import sys
import os
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any

# Add ml-service to Python path
ml_service_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml-service")
if ml_service_path not in sys.path:
    sys.path.insert(0, ml_service_path)

# Import from ML service
from app.predictions import predict_free_parking_availability

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
        # Call ML service function directly
        parking_spots = predict_free_parking_availability(lat, lon, radius_meters)
        
        return {
            "parking_spots": parking_spots,
            "count": len(parking_spots),
            "query": {"lat": lat, "lon": lon, "radius_meters": radius_meters}
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )
