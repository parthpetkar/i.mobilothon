import pandas as pd
import numpy as np
import pytz
import holidays

def preprocess_data(df):
    df = df.copy()
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    wib = pytz.timezone("Asia/Jakarta")
    # Only localize if Timestamp is naive
    if df['Timestamp'].dt.tz is None:
        df['Timestamp_WIB'] = df['Timestamp'].dt.tz_localize('UTC').dt.tz_convert(wib)
    else:
        df['Timestamp_WIB'] = df['Timestamp'].dt.tz_convert(wib)
    
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
    traffic_map = {'low':0,'medium':1,'high':2}
    
    # Use consistent hash-based encoding for SystemCodeNumber instead of dynamic mapping
    # This ensures same parking spot always gets same encoded value
    df['SystemCodeNumber'] = df['SystemCodeNumber'].apply(lambda x: hash(str(x)) % 10000).astype(int)
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
