from fastapi import APIRouter, HTTPException, Query
from app.database import client
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from math import radians, cos, sin, asin, sqrt
import joblib
import os
from datetime import datetime
import pytz
import holidays

router = APIRouter(prefix="/predictions", tags=["predictions"])

# Load ML model (cache it at module level)
_model = None
_model_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml-service", "models", "occupancy_regressor_model.joblib")

def get_model():
    global _model
    if _model is None:
        try:
            _model = joblib.load(_model_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load ML model: {str(e)}")
    return _model


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance in meters between two points."""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371000  # Radius of earth in meters
    return c * r


def preprocess_parking_data(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocess parking features for ML model prediction."""
    df = df.copy()
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    wib = pytz.timezone("Asia/Jakarta")
    df['Timestamp_WIB'] = df['Timestamp'].dt.tz_localize('UTC').dt.tz_convert(wib)
    
    # Time features
    df['Hour'] = df['Timestamp_WIB'].dt.hour
    df['DayOfWeek'] = df['Timestamp_WIB'].dt.dayofweek
    df['DayName'] = df['Timestamp_WIB'].dt.day_name()
    df['IsWeekend'] = df['DayOfWeek'].isin([5,6]).astype(int)
    
    # Holiday flag
    id_holidays = holidays.country_holidays("ID")
    df['IsHoliday'] = df['Timestamp_WIB'].dt.date.astype(str).isin(
        [str(d) for d in id_holidays]
    ).astype(int)
    
    # Time category
    def map_time_category(hour):
        if 5 <= hour < 12: return "Morning"
        if 12 <= hour < 17: return "Afternoon"
        if 17 <= hour < 21: return "Evening"
        return "Night"
    df['TimeCategory'] = df['Hour'].apply(map_time_category)
    
    # Estimated duration
    avg_duration = {
        ('Afternoon', 0, 0): 167.245646, ('Afternoon', 1, 0): 167.477519,
        ('Evening', 0, 0): 164.332264, ('Evening', 1, 0): 162.501357,
        ('Night', 0, 0): 163.594921, ('Night', 1, 0): 164.153896,
        ('Morning', 0, 0): 164.16, ('Morning', 1, 0): 164.16,
    }
    df['AvgDuration_Minutes'] = df.apply(
        lambda row: avg_duration.get((row['TimeCategory'], row['IsWeekend'], row['IsHoliday']), 164.16), axis=1
    )
    df['EstimatedDuration_Minutes'] = df['AvgDuration_Minutes'].round()
    
    # Special day flag
    df['IsSpecialDay_Flag'] = df['IsSpecialDay'].astype(int)
    
    # Mappings
    vehicle_map = {'car':0,'bike':1,'cycle':2,'truck':3}
    day_map = {'Monday':0,'Tuesday':1,'Wednesday':2,'Thursday':3,'Friday':4,'Saturday':5,'Sunday':6}
    time_map = {'Evening':0,'Night':1,'Afternoon':2,'Morning':3}
    traffic_map = {'low':0,'medium':1,'high':2, 'Light':0, 'Normal':1, 'Heavy':2, 'Congested':2}
    
    system_code_map_global = {code: idx for idx, code in enumerate(df['SystemCodeNumber'].unique())}
    df['SystemCodeNumber'] = df['SystemCodeNumber'].map(system_code_map_global).fillna(-1).astype(int)
    df['VehicleType'] = df['VehicleType'].map(vehicle_map).fillna(-1).astype(int)
    df['DayName'] = df['DayName'].map(day_map).fillna(-1).astype(int)
    df['TimeCategory'] = df['TimeCategory'].map(time_map).fillna(-1).astype(int)
    df['TrafficConditionNearby'] = df['TrafficConditionNearby'].map(traffic_map).fillna(-1).astype(int)
    
    # Sin/Cos encoding
    df['Hour_sin'] = np.sin(2*np.pi*df['Hour']/24)
    df['Hour_cos'] = np.cos(2*np.pi*df['Hour']/24)
    df['DayOfWeek_sin'] = np.sin(2*np.pi*df['DayOfWeek']/7)
    df['DayOfWeek_cos'] = np.cos(2*np.pi*df['DayOfWeek']/7)
    
    return df


@router.get("/free-parking")
async def get_free_parking_predictions(
    lat: float = Query(..., description="User latitude"),
    lon: float = Query(..., description="User longitude"),
    radius_meters: int = Query(300, description="Search radius in meters", ge=50, le=5000)
) -> Dict[str, Any]:
    """
    Get free parking availability predictions near user location.
    
    This endpoint:
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
        # Fetch all parking features from Supabase
        response = client.schema("parking").table("parking_features").select("*").execute()
        
        if not response.data:
            return {
                "parking_spots": [],
                "count": 0,
                "query": {"lat": lat, "lon": lon, "radius_meters": radius_meters}
            }
        
        df = pd.DataFrame(response.data)
        
        # Store original SystemCodeNumber before preprocessing
        original_system_codes = df['SystemCodeNumber'].copy()
        
        # Filter by distance
        df['distance'] = df.apply(
            lambda row: haversine_distance(lat, lon, row['Latitude'], row['Longitude']), 
            axis=1
        )
        df = df[df['distance'] <= radius_meters]
        
        if df.empty:
            return {
                "parking_spots": [],
                "count": 0,
                "query": {"lat": lat, "lon": lon, "radius_meters": radius_meters}
            }
        
        # Preprocess data
        processed_data = preprocess_parking_data(df)
        
        # Extract model-required features
        feature_cols = [
            'SystemCodeNumber', 'Capacity', 'DayName', 'VehicleType', 'TrafficConditionNearby',
            'IsSpecialDay', 'Hour', 'DayOfWeek', 'IsWeekend', 'IsHoliday', 'TimeCategory',
            'EstimatedDuration_Minutes', 'IsSpecialDay_Flag', 'Hour_sin', 'Hour_cos',
            'DayOfWeek_sin', 'DayOfWeek_cos'
        ]
        
        for col in feature_cols:
            if col not in processed_data.columns:
                processed_data[col] = 0
        
        X_predict = processed_data[feature_cols]
        
        # Load model and predict
        model = get_model()
        predicted_occupancy = model.predict(X_predict)
        
        processed_data['PredOccupancy'] = predicted_occupancy.round()
        processed_data['PredOccupancy_Ratio'] = processed_data['PredOccupancy'] / processed_data['Capacity']
        processed_data['PredOccupancy_Ratio'] = processed_data['PredOccupancy_Ratio'].clip(0, 1)
        
        # Calculate availability probability (1 - occupancy ratio)
        processed_data['availability_probability'] = 1 - processed_data['PredOccupancy_Ratio']
        
        # Build response
        parking_spots = []
        for idx, row in processed_data.iterrows():
            # Get original SystemCodeNumber from the same index
            original_code = original_system_codes.loc[idx]
            
            parking_spots.append({
                "systemCode": str(original_code),
                "lat": float(row['Latitude']),
                "lon": float(row['Longitude']),
                "availabilityProbability": float(row['availability_probability']),
                "radius": radius_meters
            })
        
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
