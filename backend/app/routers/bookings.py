from fastapi import APIRouter, Depends, HTTPException
from app.models import BookingCreate, BookingUpdate, BookingResponse
from app.database import create_booking, get_bookings_by_user, get_booking_by_id, update_booking, delete_booking
from app.dependencies import get_current_user
from typing import List, Dict
from app.redis_client import redis_client
from pydantic import BaseModel


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


class VerifyOTPRequest(BaseModel):
    otp: str


@router.post("/{booking_id}/verify-otp")
async def verify_otp_endpoint(booking_id: int, request: VerifyOTPRequest, current_user: Dict = Depends(get_current_user)):
    """
    Verify OTP for a booking. Seller uses this to confirm customer entry.
    """
    from app.database import client
    
    # Get the booking
    booking_response = client.table("bookings").select("*").eq("id", booking_id).execute()
    
    if not booking_response.data:
        raise HTTPException(404, "Booking not found")
    
    booking = booking_response.data[0]
    
    # Verify that the current user is the seller (operator) of the parking
    parking_response = client.table("parkings").select("operator_id").eq("id", booking["parking_id"]).execute()
    
    if not parking_response.data:
        raise HTTPException(404, "Parking not found")
    
    parking = parking_response.data[0]
    
    if parking["operator_id"] != current_user["email"]:
        raise HTTPException(403, "Only the parking operator can verify OTPs")
    
    # Verify OTP
    if booking.get("otp") != request.otp:
        raise HTTPException(400, "Invalid OTP")
    
    # Mark booking as verified/active
    client.table("bookings").update({"status": "ACTIVE"}).eq("id", booking_id).execute()
    
    return {
        "message": "OTP verified successfully",
        "booking_id": booking_id,
        "customer": booking["user_id"]
    }
