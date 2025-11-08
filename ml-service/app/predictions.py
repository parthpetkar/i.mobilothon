from .preprocessing import preprocess_data
from .models import loaded_occupancy_model
import numpy as np
import pandas as pd
from typing import List, Dict
from math import radians, cos, sin, asin, sqrt

BASE_PRICE_PER_HOUR = 10.0

def traffic_multiplier(traffic_str):
    if traffic_str == 'high': return 1.4
    if traffic_str in ['medium', 'average']: return 1.15
    return 1.0

def event_multiplier(is_special):
    return 1.3 if is_special else 1.0

def dynamic_price(row, base=BASE_PRICE_PER_HOUR):
    dfactor = 1.0 + row['PredOccupancy_Ratio']
    tmult = traffic_multiplier(row['TrafficConditionNearby'])
    emult = event_multiplier(row['IsSpecialDay'])
    return base * dfactor * tmult * emult

def predict_parking_dynamics(raw_data_df):
    processed_data = preprocess_data(raw_data_df)
    
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
    predicted_occupancy = loaded_occupancy_model.predict(X_predict)
    processed_data['PredOccupancy'] = predicted_occupancy.round()
    processed_data['PredOccupancy_Ratio'] = processed_data['PredOccupancy']/processed_data['Capacity']
    processed_data['PredOccupancy_Ratio'] = processed_data['PredOccupancy_Ratio'].clip(0,1)
    
    # Map traffic back to string for price calculation
    reverse_traffic_map = {0:'low',1:'medium',2:'high'}
    # Create a temporary column with string traffic for price calculation
    processed_data['TrafficConditionNearby_Str'] = processed_data['TrafficConditionNearby'].map(reverse_traffic_map).fillna('low')
    
    # Calculate dynamic price using string traffic condition
    def apply_dynamic_price(row):
        # Create a modified row with string traffic for price calculation
        price_row = row.copy()
        price_row['TrafficConditionNearby'] = price_row['TrafficConditionNearby_Str']
        return dynamic_price(price_row, base=BASE_PRICE_PER_HOUR)
    
    processed_data['PredictedDynamicPricePerHour'] = processed_data.apply(apply_dynamic_price, axis=1)
    
    return processed_data


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance in meters between two points 
    on the earth (specified in decimal degrees).
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Radius of earth in meters
    r = 6371000
    return c * r


def predict_free_parking_availability(
    user_lat: float,
    user_lon: float
) -> List[Dict]:
    """
    Predict free parking availability for parking spots near user location.
    Each parking spot's availability radius is dynamically computed based on predicted occupancy:
    - Low occupancy (< 0.3): 1500m radius
    - Medium occupancy (0.3-0.6): 800m radius  
    - High occupancy (> 0.6): 300m radius
    
    Args:
        user_lat: User's latitude
        user_lon: User's longitude
    
    Returns:
        List of parking spots with availability predictions and dynamic radius
    """
    from .config import supabase
    
    # Fetch all parking features from Supabase
    response = supabase.schema("parking").table("parking_features").select("*").execute()
    if not response.data:
        return []
    df = pd.DataFrame(response.data)
    # Store original SystemCodeNumber before preprocessing
    df['OriginalSystemCode'] = df['SystemCodeNumber'].copy()
    
    # Prepare features for prediction (reuse existing preprocessing)
    processed_data = preprocess_data(df)
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
    # Predict occupancy
    predicted_occupancy = loaded_occupancy_model.predict(X_predict)
    processed_data['PredOccupancy'] = predicted_occupancy.round()
    processed_data['PredOccupancy_Ratio'] = processed_data['PredOccupancy'] / processed_data['Capacity']
    processed_data['PredOccupancy_Ratio'] = processed_data['PredOccupancy_Ratio'].clip(0, 1)
    
    # Calculate availability probability (1 - occupancy ratio)
    processed_data['availability_probability'] = 1 - processed_data['PredOccupancy_Ratio']
    
    # Compute ML-based availability_radius based on predicted occupancy
    def compute_availability_radius(pred_occupancy_ratio: float) -> int:
        """
        Compute dynamic availability radius based on predicted occupancy:
        - Low occupancy (< 0.3): 1500m radius (more space available)
        - Medium occupancy (0.3-0.6): 800m radius (moderate space)
        - High occupancy (> 0.6): 300m radius (limited space)
        """
        if pred_occupancy_ratio < 0.3:
            return 1500
        elif pred_occupancy_ratio <= 0.6:
            return 800
        else:
            return 300
    
    processed_data['availability_radius'] = processed_data['PredOccupancy_Ratio'].apply(compute_availability_radius)
    
    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Predictions summary: Capacity avg={processed_data['Capacity'].mean():.1f}, "
                f"PredOccupancy avg={processed_data['PredOccupancy'].mean():.1f}, "
                f"Availability avg={processed_data['availability_probability'].mean():.3f}, "
                f"Radius avg={processed_data['availability_radius'].mean():.1f}m")
    
    # Build response
    results = []
    for _, row in processed_data.iterrows():
        results.append({
            "systemCode": str(row['OriginalSystemCode']),
            "lat": float(row['Latitude']),
            "lon": float(row['Longitude']),
            "availabilityProbability": float(row['availability_probability']),
            "radius": int(row['availability_radius'])  # Use ML-computed radius
        })
    return results
