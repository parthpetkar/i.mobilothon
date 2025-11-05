from fastapi import APIRouter, Depends, HTTPException
from app.models import BookingCreate, BookingUpdate, BookingResponse
from app.database import create_booking, get_bookings_by_user, get_booking_by_id, update_booking, delete_booking
from app.dependencies import get_current_user
from typing import List, Dict
from app.redis_client import redis_client


router = APIRouter(prefix="/bookings", tags=["bookings"])

@router.post("/", response_model=dict)
async def create_booking_endpoint(booking: BookingCreate, current_user: Dict = Depends(get_current_user)):
    # Ignore booking.userId if present; use token
    try: 
        db_booking = await create_booking(booking, current_user["email"], redis_client)
        return {
            "message": "Booking created successfully",
            "booking": BookingResponse(**db_booking)
        }
    except ValueError as e:
        if str(e) == "Could not acquire lock - try again":
            raise HTTPException(status_code=429, detail="System is busy. Please try again in a moment.")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[BookingResponse])
async def get_bookings(current_user: Dict = Depends(get_current_user)):
    bookings = await get_bookings_by_user(current_user["email"])
    return [BookingResponse(**b) for b in bookings]

@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: int, current_user: Dict = Depends(get_current_user)):
    booking = await get_booking_by_id(booking_id, current_user["email"])
    if not booking:
        raise HTTPException(404, "Booking not found")
    return BookingResponse(**booking)

@router.put("/{booking_id}", response_model=dict)
async def update_booking_endpoint(booking_id: int, update: BookingUpdate, current_user: Dict = Depends(get_current_user)):
    update_dict = {"end_time": update.endTime.isoformat()} if update.endTime else {}
    if not update_dict:
        raise HTTPException(400, "No updates provided")
    db_booking = await update_booking(booking_id, update_dict, current_user["email"])
    return {
        "message": "Booking updated successfully",
        "booking": BookingResponse(**db_booking)
    }

@router.delete("/{booking_id}")
async def delete_booking_endpoint(booking_id: int, current_user: Dict = Depends(get_current_user)):
    if await delete_booking(booking_id, current_user["email"]):
        return {"message": "Booking canceled successfully"}
    raise HTTPException(404, "Booking not found")