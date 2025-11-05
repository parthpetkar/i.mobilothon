from .preprocessing import preprocess_data
from .models import loaded_occupancy_model
import numpy as np

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
    
    reverse_traffic_map = {0:'low',1:'medium',2:'high'}
    processed_data['TrafficConditionNearby_Category'] = processed_data['TrafficConditionNearby'].map(reverse_traffic_map)
    processed_data['PredictedDynamicPricePerHour'] = processed_data.apply(
        lambda row: dynamic_price(row, base=BASE_PRICE_PER_HOUR), axis=1
    )
    
    return processed_data
