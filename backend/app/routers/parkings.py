from fastapi import APIRouter, Depends, HTTPException, Query
from app.models import ParkingCreate, ParkingUpdate, ParkingAvailabilityUpdate, ParkingResponse
from app.database import create_parking, get_parkings_near, get_parking_by_id, update_parking, delete_parking, update_availability
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
        # RPC should return 'location' as list; ensure floats
        if "location" in p_copy and isinstance(p_copy["location"], list):
            p_copy["location"] = [float(l) for l in p_copy["location"]]
        else:
            # Fallback: Extract from geom if RPC fails (add ST_X/ST_Y in RPC)
            from app.database import client
            geom_resp = client.rpc("ST_AsText", {"geom": p_copy.get("geom", "POINT(0 0)")}).execute()
            if geom_resp.data:
                # Parse 'POINT(lng lat)' – simplistic
                point_str = geom_resp.data[0].get("st_astext", "POINT(0 0)")
                coords = point_str.replace("POINT(", "").replace(")", "").split()
                p_copy["location"] = [float(coords[0]), float(coords[1])] if len(coords) == 2 else [0.0, 0.0]
            del p_copy["geom"]  # Clean up if present
        p_copy["price_per_hour"] = Decimal(str(p_copy.get("price_per_hour", 0)))  # Map to Decimal
        # if "price_per_hour" in p_copy:
        #     del p_copy["price_per_hour"]
        processed.append(ParkingResponse(**p_copy))
    
    return processed

# @router.post("/", response_model=dict)
@router.post("/", response_model=Dict[str, ParkingResponse])
async def create_parking_endpoint(parking: ParkingCreate, current_user: Dict = Depends(get_current_seller)):
    db_parking = await create_parking(parking, current_user["id"])
    
    new_parking = {
        "id": db_parking["id"],
        "name": db_parking["name"],
        "location": db_parking.get("geom", {}).get("coordinates", []),
        "price_per_hour": db_parking.get("price_per_hour", 0),
        "slots": db_parking["slots"],
        "available": db_parking["available"],
        "amenities": db_parking.get("amenities", []),
        "rating": db_parking.get("rating", 0),
    }

    return {"parking": ParkingResponse(**new_parking)}

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