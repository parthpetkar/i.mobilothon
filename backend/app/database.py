from supabase import create_client, Client
from app.config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY
from app.models import ParkingCreate, BookingCreate
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import random
from app.redis_client import acquire_lock, release_lock, acquire_lock_with_retry

# client: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
client: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

async def get_user_profile(user_id: str) -> Dict[str, Any]:
    response = client.table("profiles").select("*").eq("id", user_id).execute()
    return response.data[0] if response.data else {}

async def create_parking(create_data: ParkingCreate, operator_id: str) -> Dict[str, Any]:
    data = {
        "name": create_data.name,
        "operator_id": operator_id,
        "geom": {
            "type": "Point",
            "coordinates": [create_data.location[0], create_data.location[1]]
        },
        # Price may be None initially; store NULL in DB if not provided
        # Set default price of 0 until ML service updates it
        "price_per_hour": float(create_data.price_per_hour if create_data.price_per_hour is not None else 0),
        "slots": create_data.slots,
        "available": create_data.slots,
        "amenities": create_data.amenities or [],
        "rating": 0.00
    }
    response = client.table("parkings").insert(data).execute()
    if response.data:
        print(f"Event: listing.created - ID: {response.data[0]['id']}")
        return response.data[0]
    raise ValueError("Failed to create parking")


async def set_price_for_parking(parking_id: int, price: float) -> Dict[str, Any]:
    """Update price_per_hour for a parking without checking operator ownership.

    This is intended to be called by the ML callback service which has its own
    auth/validation handled at the router level.
    """
    response = client.table("parkings").update({"price_per_hour": price}).eq("id", parking_id).execute()
    if response.data:
        print(f"Event: listing.price_updated - ID: {parking_id}")
        return response.data[0]
    raise ValueError("Failed to set price for parking")


async def get_parkings_near(query: Dict[str, Any]) -> List[Dict[str, Any]]:
    response = client.rpc("get_parkings_near_location", {
        "center_lng": query["location"][0],
        "center_lat": query["location"][1],
        "radius_meters": query["radius"],
        "price_min": float(query["price_min"]),
        "price_max": float(query["price_max"])
    }).execute()
    return response.data or []

async def get_parking_by_id(parking_id: int) -> Optional[Dict[str, Any]]:
    response = client.table("parkings").select("*").eq("id", parking_id).execute()
    return response.data[0] if response.data else None

async def update_parking(parking_id: int, update_data: Dict[str, Any], operator_id: str) -> Dict[str, Any]:
    print("update_data:", update_data)
    print("operator_id:", operator_id)
    print("parking_id:", parking_id)

    response = client.table("parkings").update(update_data).eq("id", parking_id).eq("operator_id", operator_id).execute()
    if response.data:
        print(f"Event: listing.updated - ID: {parking_id}")
        if "slots" in update_data:
            client.table("parkings").update({"available": update_data["slots"] - (await count_confirmed_bookings(parking_id))}).eq("id", parking_id).execute()  # Adjust available
        return response.data[0]
    raise ValueError("Failed to update parking")

async def delete_parking(parking_id: int, operator_id: str) -> bool:
    response = client.table("parkings").delete().eq("id", parking_id).eq("operator_id", operator_id).execute()
    return bool(response.data)

async def update_availability(parking_id: int, available: int, operator_id: str) -> Dict[str, Any]:
    response = client.table("parkings").update({"available": available}).eq("id", parking_id).eq("operator_id", operator_id).execute()
    return response.data[0] if response.data else {}

# Helper for count
async def count_confirmed_bookings(parking_id: int) -> int:
    response = client.rpc("count_overlapping_bookings", {
        "parking_id": parking_id,
        "start_time": "1900-01-01T00:00:00Z",  # All time
        "end_time": "2100-01-01T00:00:00Z"
    }).execute()
    return response.data[0]["count"] if response.data else 0

# Bookings
async def create_booking(create_data: BookingCreate, user_id: str, redis_client) -> Dict[str, Any]:
    parking = await get_parking_by_id(create_data.parkingId)
    if not parking:
        raise ValueError("Parking not found")

    lock_key = f"lock:booking:{create_data.parkingId}:{create_data.startTime.isoformat()}"
    lock_id = await acquire_lock_with_retry(redis_client, lock_key)
    if not lock_id:
        raise ValueError("Could not acquire lock - try again")

    try:
        overlap_response = client.rpc("count_overlapping_bookings", {
            "p_parking_id": create_data.parkingId,
            "p_start_time": create_data.startTime.isoformat(),
            "p_end_time": create_data.endTime.isoformat()
        }).execute()

        overlap = overlap_response.data[0]["count"] if overlap_response.data else 0
        print("overlap: ", overlap)
        print("Available: " , parking["available"])
        if overlap >= parking["available"]:
            raise ValueError("No available slots")

        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))

        data = {
            "parking_id": create_data.parkingId,
            "user_id": user_id,
            "start_time": create_data.startTime.isoformat(),
            "end_time": create_data.endTime.isoformat(),
            "status": "CONFIRMED",  # <-- uppercase
            "otp": otp
        }
        response = client.table("bookings").insert(data).execute()
        if response.data:
            print(f"Event: booking.created - ID: {response.data[0]['id']}, OTP: {otp}")
            return response.data[0]
        raise ValueError("Failed to create booking")
    finally:
        await release_lock(redis_client, lock_key, lock_id)


async def get_bookings_by_user(user_id: str) -> List[Dict[str, Any]]:
    response = client.table("bookings").select("*").eq("user_id", user_id).execute()
    return response.data or []

async def get_booking_by_id(booking_id: int, user_id: str) -> Optional[Dict[str, Any]]:
    response = client.table("bookings").select("*").eq("id", booking_id).eq("user_id", user_id).execute()
    return response.data[0] if response.data else None

async def update_booking(booking_id: int, update_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    response = client.table("bookings").update(update_data).eq("id", booking_id).eq("user_id", user_id).execute()
    if response.data:
        print(f"Event: booking.updated - ID: {booking_id}")
        return response.data[0]
    raise ValueError("Failed to update booking")

async def delete_booking(booking_id: int, user_id: str) -> bool:
    response = client.table("bookings").delete().eq("id", booking_id).eq("user_id", user_id).execute()
    if response.data:
        print(f"Event: booking.cancelled - ID: {booking_id}")
        return True
    return False

# Seller
async def get_analytics(user_id: str) -> Dict[str, Any]:
    response = client.rpc("get_seller_analytics", {"seller_id": user_id}).execute()

    # Since your RPC returns a single JSON object
    if isinstance(response.data, dict):
        return response.data
    elif isinstance(response.data, list) and len(response.data) > 0:
        return response.data[0]
    else:
        return {"totalRevenue": 0, "avgOccupancy": 0, "totalListings": 0}


async def get_seller_parkings(user_id: str) -> List[Dict[str, Any]]:
    response = client.rpc("get_seller_parkings", {"seller_id": user_id}).execute()
    return response.data or []