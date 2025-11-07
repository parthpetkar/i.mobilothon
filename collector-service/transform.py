"""
Data Transformation Module

Transforms collected parking data into machine learning features.
Includes timezone conversion, time-based features, and duration calculations.
"""

import pandas as pd
import numpy as np
import pytz
import holidays
from datetime import datetime
from typing import Dict, List, Any
import logging
from supabase import create_client
from supabase.client import ClientOptions

logger = logging.getLogger(__name__)

# Indian holidays calendar
indian_holidays = holidays.India()


def transform_parking_data(
    places_data: Dict[str, Any],
    traffic_data: Dict[str, Any],
    weather_data: Dict[str, Any],
    events_data: Dict[str, Any]
) -> pd.DataFrame:
    """
    Transform collected data into parking features.
    Supports both parking mode and commercial places mode.
    
    Args:
        places_data: Places data from places collector (format: {'items': [...]})
        traffic_data: Traffic data from traffic collector
        weather_data: Weather data from weather collector
        events_data: Events data from events collector
        
    Returns:
        DataFrame with transformed parking features
    """
    logger.info("Starting data transformation...")
    
    # Step 1: Create records from collected data
    all_records = []
    
    # Create traffic condition lookup for grid-based traffic data
    traffic_lookup = {}
    for item in traffic_data.get('items', []):
        grid_id = item.get('grid_id')
        traffic_info = item.get('data', {})
        # Extract duration from routing response if available
        duration = None
        try:
            features = traffic_info.get('features', [])
            if features:
                properties = features[0].get('properties', {})
                time_info = properties.get('time')
                if time_info:
                    duration = time_info / 60  # Convert seconds to minutes
        except (KeyError, TypeError, IndexError):
            pass
        
        # Categorize traffic condition based on duration
        if duration is None:
            condition = "Normal"
        elif duration < 5:
            condition = "Light"
        elif duration < 15:
            condition = "Normal"
        elif duration < 30:
            condition = "Heavy"
        else:
            condition = "Congested"
            
        traffic_lookup[grid_id] = condition
    
    # Flatten places data into records
    for item in places_data.get('items', []):
        centroid = item.get('centroid', [0, 0])
        grid_id = item.get('grid_id')
        mode = item.get('mode', 'unknown')  # 'parking' or 'commercial'
        
        for place in item.get('places', []):
            place_id = place.get('id')
            if place_id is None:
                continue  # Skip places without IDs
                
            # Generate SystemCodeNumber based on mode and source
            if mode == 'parking':
                # Parking mode - use OSM_<id> format
                system_code = place_id  # Already formatted as OSM_<id> from collector
                vehicle_type = 'car'
                capacity = 0  # Default to 0 for parking mode
                queue_length = 0
                is_special_day = 0
            else:
                # Commercial places mode - simulate parking characteristics
                system_code = f"COMM_{place_id}"  # Commercial place as parking proxy
                vehicle_type = 'car'
                capacity = np.random.randint(20, 200)  # Simulated capacity for commercial areas
                queue_length = np.random.randint(0, 10)
                is_special_day = 0
            
            # Get traffic condition for this grid
            traffic_condition = traffic_lookup.get(grid_id, "Normal")
            
            record = {
                'SystemCodeNumber': system_code,
                'Capacity': capacity,
                'Latitude': place.get('lat', centroid[1]),
                'Longitude': place.get('lon', centroid[0]),
                'VehicleType': vehicle_type,
                'TrafficConditionNearby': traffic_condition,
                'QueueLength': queue_length,
                'IsSpecialDay': is_special_day,
                'Timestamp': datetime.utcnow().isoformat() + 'Z'  # Current UTC timestamp
            }
            all_records.append(record)
    
    if not all_records:
        logger.warning("No data to transform")
        return pd.DataFrame()
    
    df = pd.DataFrame(all_records)
    logger.info(f"Created {len(df)} feature records")
    
    # Step 2: Apply existing time transformations
    df = _add_time_features(df)
    
    # Step 3: Add existing duration features
    df = _add_duration_features(df)
    
    # Step 4: Format final output using existing logic
    df = _format_final_columns(df)
    
    logger.info(f"Transformation complete. Generated {len(df)} records")
    return df


def _add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add time-based features with Indian timezone."""
    logger.info("Adding time features...")
    
    if df.empty:
        return df
    
    # Convert to Indian Standard Time (IST)
    india_tz = pytz.timezone('Asia/Kolkata')
    india_holidays = holidays.country_holidays("IN")
    
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Timestamp_WIB'] = df['Timestamp'].dt.tz_localize('UTC').dt.tz_convert(india_tz)
    
    # Extract time features
    df['Hour'] = df['Timestamp_WIB'].dt.hour.astype(int)
    df['DayOfWeek'] = df['Timestamp_WIB'].dt.dayofweek.astype(int)
    df['DayName'] = df['Timestamp_WIB'].dt.day_name()
    df['IsWeekend'] = df['DayOfWeek'].isin([5, 6]).astype(int)
    df['IsHoliday'] = df['Timestamp_WIB'].apply(
        lambda x: 1 if x.date() in india_holidays else 0
    )
    
    # Time category
    df['TimeCategory'] = df['Hour'].apply(_categorize_time)
    
    logger.info("Time features added successfully")
    return df


def _categorize_time(hour: int) -> str:
    """Categorize hour into time periods."""
    if 5 <= hour < 12:
        return 'Morning'
    elif 12 <= hour < 17:
        return 'Afternoon'
    elif 17 <= hour < 21:
        return 'Evening'
    else:
        return 'Night'


def _add_duration_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add parking duration features."""
    logger.info("Calculating parking durations...")
    
    if df.empty:
        return df
    
    # Random duration between 30 minutes to 5 hours (in minutes)
    random_minutes = np.random.randint(30, 301, size=len(df))
    df['Duration_Minutes'] = random_minutes
    
    # Estimated duration by group
    group_cols = ['TimeCategory', 'IsWeekend', 'IsHoliday']
    avg_duration = df.groupby(group_cols)['Duration_Minutes'].mean().reset_index()
    avg_duration.rename(columns={'Duration_Minutes': 'EstimatedDuration_Minutes'}, inplace=True)
    df = df.merge(avg_duration, on=group_cols, how='left')
    df['EstimatedDuration_Minutes'] = df['EstimatedDuration_Minutes'].round().astype(int)
    
    logger.info("Duration features calculated")
    return df


def _format_final_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Format and select final columns for output."""
    logger.info("Formatting final columns...")
    
    if df.empty:
        return df
    
    # Format timestamps
    df['Timestamp'] = df['Timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df['Timestamp_WIB'] = df['Timestamp_WIB'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Add ID column
    df.insert(0, 'ID', range(1, len(df) + 1))
    
    # Select final columns
    final_columns = [
        'ID', 'SystemCodeNumber', 'Capacity', 'Latitude', 'Longitude',
        'Occupancy', 'VehicleType', 'TrafficConditionNearby', 'QueueLength',
        'IsSpecialDay', 'Timestamp', 'Timestamp_WIB', 'Hour', 'DayOfWeek',
        'DayName', 'IsWeekend', 'IsHoliday', 'TimeCategory',
        'Duration_Minutes', 'EstimatedDuration_Minutes'
    ]
    
    df = df[final_columns]
    
    logger.info("Final formatting complete")
    return df


def prepare_for_supabase(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Prepare transformed data for Supabase insertion.
    
    Args:
        df: Transformed DataFrame
        
    Returns:
        List of dictionaries ready for Supabase insertion
    """
    logger.info("Preparing data for Supabase...")
    
    if df.empty:
        return []
    
    # Convert to dict and handle numpy types
    records = df.to_dict('records')
    # Cast NumPy dtypes to native Python types for JSON/Supabase compatibility
    records = [
        {
            k: (
                int(v) if isinstance(v, (np.integer, np.int64)) else
                float(v) if isinstance(v, (np.floating, np.float64)) else
                bool(v) if isinstance(v, (np.bool_, bool)) else
                v
            )
            for k, v in record.items()
        }
        for record in records
    ]
    
    logger.info(f"Prepared {len(records)} records for Supabase")
    return records


def save_to_supabase(
    records: List[Dict[str, Any]],
    supabase_url: str,
    supabase_key: str,
    batch_size: int = 1000,
    max_records: int = None
) -> int:
    """
    Save transformed records to Supabase.
    
    Args:
        records: List of records to save
        supabase_url: Supabase project URL
        supabase_key: Supabase API key
        batch_size: Number of records per batch
        max_records: Maximum number of records to save (None = save all)
        
    Returns:
        Number of records saved
        
    Raises:
        Exception: If save operation fails
    """
    try:
        supabase = create_client(
            supabase_url,
            supabase_key,
            options=ClientOptions(schema="parking")  # <- set schema here
        )
        
        # Limit records if specified
        if max_records is not None and max_records > 0:
            records = records[:max_records]
            logger.info(f"Limited to {len(records)} records (max_records={max_records})")
        
        logger.info(f"Connecting to Supabase and saving {len(records)} records...")
        
        supabase = create_client(supabase_url, supabase_key)
        records_saved = 0
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            resp = supabase.schema("parking").table("parking_features").insert(batch).execute()
            # optional: check resp for errors
            if getattr(resp, "error", None):
                raise Exception(f"Supabase insert error: {resp.error}")
            records_saved += len(batch)
        return records_saved
        
    except Exception as e:
        logger.error(f"Error saving to Supabase: {str(e)}")
        raise
