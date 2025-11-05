from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class ParkingCreate(BaseModel):
    name: str
    location: List[float] = Field(..., min_items=2, max_items=2)  # [lng, lat]
    price_per_hour: Decimal = Field(..., ge=0)
    slots: int = Field(1, ge=1)
    amenities: Optional[List[str]] = []

class ParkingUpdate(BaseModel):
    name: Optional[str] = None
    price_per_hour: Optional[Decimal] = None
    slots: Optional[int] = None
    amenities: Optional[List[str]] = None

class ParkingAvailabilityUpdate(BaseModel):
    available: int = Field(..., ge=0)

class ParkingResponse(BaseModel):
    id: int
    name: str
    location: List[float]
    price_per_hour: Decimal
    slots: int
    available: int
    amenities: List[str]
    rating: Optional[Decimal] = Field(0.00, ge=0, le=5)

    class Config:  # Fixed indentation
        from_attributes = True

class BookingCreate(BaseModel):
    parkingId: int
    startTime: datetime
    endTime: datetime

    @model_validator(mode='after')
    def check_time_order(self):
        if self.endTime <= self.startTime:
            raise ValueError("endTime must be greater than startTime")
        return self

class BookingUpdate(BaseModel):
    endTime: Optional[datetime] = None

class BookingResponse(BaseModel):
    id: int
    parkingId: int = Field(..., alias="parking_id")
    startTime: datetime = Field(..., alias="start_time")
    endTime: datetime = Field(..., alias="end_time")
    status: str = "confirmed"

    class Config:
        from_attributes = True
        populate_by_name = True  # allow both snake_case and camelCase

class AnalyticsResponse(BaseModel):
    totalRevenue: Decimal
    avgOccupancy: Decimal
    totalListings: int

class SellerParkingResponse(BaseModel):
    id: int
    name: str
    price: Decimal
    slots: int
    available: int
    daily_revenue: Decimal
    rating: Optional[Decimal] = Field(0.00, ge=0, le=5)

    class Config:  # Fixed indentation
        from_attributes = True