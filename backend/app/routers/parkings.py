from fastapi import APIRouter, Depends, HTTPException, Query, Header, Body
from app.models import ParkingCreate, ParkingUpdate, ParkingAvailabilityUpdate, ParkingResponse
from app.database import (
    create_parking,
    get_parkings_near,
    get_parking_by_id,
    update_parking,
    delete_parking,
    update_availability,
    set_price_for_parking,
)
from app.config import COLLECTOR_SERVICE_URL, ML_CALLBACK_SECRET
import httpx
from app.dependencies import get_current_seller
from typing import List, Dict
from decimal import Decimal

router = APIRouter(prefix="/parkings", tags=["parkings"])

@router.get("/", response_model=List[ParkingResponse])
async def get_parkings(  # Now async
    location: List[float] = Query(
        ...,
        description="Location as [longitude, latitude] – use repeated: location=lng&location=lat",
        min_items=2,
        max_items=2
    ),
    radius: int = Query(1000, ge=1, le=50000, description="Radius in meters"),
    price_min: float = Query(0.0, ge=0.0, description="Min price per hour"),
    price_max: float = Query(99999.0, ge=0.0, description="Max price per hour")
):
    if len(location) != 2:
        raise HTTPException(status_code=422, detail="Location must be exactly [lng, lat]")
    
    # Public, no auth
    query = {"location": location, "radius": radius, "price_min": price_min, "price_max": price_max}
    parkings_data = await get_parkings_near(query)  # Await fixed
    
    # Process: Ensure location is List[float], map price_per_hour to price
    processed = []
    for p in parkings_data:
        p_copy = p.copy()
        
        if isinstance(p_copy.get("location"), list):
            p_copy["location"] = [float(x) for x in p_copy["location"]]
        
        price = p_copy.get("price_per_hour", 0)
        p_copy["price_per_hour"] = Decimal(str(price))

        processed.append(ParkingResponse(**p_copy))
        
    return processed

# @router.post("/", response_model=dict)
@router.post("/", response_model=Dict[str, ParkingResponse])
async def create_parking_endpoint(parking: ParkingCreate, current_user: Dict = Depends(get_current_seller)):
    # Create listing in main DB. Price may be None initially (ML will set it later).
    db_parking = await create_parking(parking, current_user["id"])

    new_parking = {
        "id": db_parking["id"],
        "name": db_parking["name"],
        "location": db_parking.get("geom", {}).get("coordinates", []),
        # Ensure response model gets a Decimal-like numeric value even if None
        "price_per_hour": db_parking.get("price_per_hour") if db_parking.get("price_per_hour") is not None else 0,
        "slots": db_parking["slots"],
        "available": db_parking["available"],
        "amenities": db_parking.get("amenities", []),
        "rating": db_parking.get("rating", 0),
    }

    # Forward a simplified record to the collector service so it can store features for ML
    try:
        collector_payload = {
            "parking_id": db_parking["id"],
            "name": db_parking["name"],
            "location": db_parking.get("geom", {}).get("coordinates", []),
            "slots": db_parking["slots"],
            "amenities": db_parking.get("amenities", []),
            "operator_id": current_user["id"]
        }
        async with httpx.AsyncClient(timeout=10) as client:
            collector_url = f"{COLLECTOR_SERVICE_URL.rstrip('/')}/ingest/parking"
            resp = await client.post(collector_url, json=collector_payload)
            if resp.status_code >= 400:
                # log but do not fail the whole request - ML pipeline is asynchronous
                print(f"Collector ingestion failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"Error forwarding to collector: {str(e)}")

    return {"parking": ParkingResponse(**new_parking)}


@router.post("/{parking_id}/price-callback", response_model=Dict[str, ParkingResponse])
async def ml_price_callback(parking_id: int, payload: Dict = Body(...), x_ml_secret: str = Header(None)):
    """Endpoint for ML service to POST computed price for a parking listing.

    Expects header 'X-ML-Secret' to match ML_CALLBACK_SECRET.
    Body: { "price_per_hour": 123.45 }
    """
    # Validate secret
    if ML_CALLBACK_SECRET is None or x_ml_secret != ML_CALLBACK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid ML callback secret")

    if not payload or "price_per_hour" not in payload:
        raise HTTPException(status_code=400, detail="Missing price_per_hour in payload")

    try:
        price_val = float(payload["price_per_hour"])
    except Exception:
        raise HTTPException(status_code=400, detail="price_per_hour must be a number")

    # Update DB without operator check
    db_parking = await set_price_for_parking(parking_id, price_val)

    formatted_parking = {
        "id": db_parking["id"],
        "name": db_parking["name"],
        "location": db_parking.get("geom", {}).get("coordinates", []),
        "price_per_hour": db_parking.get("price_per_hour", 0),
        "slots": db_parking.get("slots", 0),
        "available": db_parking.get("available", 0),
        "amenities": db_parking.get("amenities", []),
        "rating": db_parking.get("rating", 0),
    }

    return {"parking": ParkingResponse(**formatted_parking)}

@router.put("/{parking_id}", response_model=dict)
async def update_parking_endpoint(parking_id: int, parking: ParkingUpdate, current_user: Dict = Depends(get_current_seller)):
    if not parking.dict(exclude_unset=True):
        raise HTTPException(400, "No updates provided")

    update_dict = {
        k: float(v) if isinstance(v, Decimal) else v
        for k, v in parking.dict(exclude_unset=True).items()
    }

    db_parking = await update_parking(parking_id, update_dict, current_user["id"])

    # 🧠 Map Supabase response → ParkingResponse schema
    formatted_parking = {
        "id": db_parking["id"],
        "name": db_parking["name"],
        "location": db_parking.get("geom", {}).get("coordinates", []),
        "price_per_hour": db_parking.get("price_per_hour", 0),
        "slots": db_parking["slots"],
        "available": db_parking["available"],
        "amenities": db_parking.get("amenities", []),
        "rating": db_parking.get("rating", 0),
    }

    return {
        "message": "Parking spot updated successfully",
        "parking": ParkingResponse(**formatted_parking)
    }

@router.delete("/{parking_id}")
async def delete_parking_endpoint(parking_id: int, current_user: Dict = Depends(get_current_seller)):
    if await delete_parking(parking_id, current_user["id"]):
        return {"message": "Parking spot deleted successfully"}
    raise HTTPException(404, "Parking not found")

@router.put("/{parking_id}/availability", response_model=dict)
async def update_availability_endpoint(parking_id: int, avail: ParkingAvailabilityUpdate, current_user: Dict = Depends(get_current_seller)):
    db_parking = await update_availability(parking_id, avail.available, current_user["id"])
    return {
        "message": "Availability updated successfully",
        "parking": {"id": db_parking["id"], "available": db_parking["available"]}
    }