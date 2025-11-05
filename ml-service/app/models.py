import joblib

# Load models
try:
    loaded_occupancy_model = joblib.load('./models/occupancy_regressor_model.joblib')
    # loaded_dynamic_price_model = joblib.load('dynamic_price_model.joblib')
    print("Models loaded successfully.")
except FileNotFoundError as e:
    print(f"Error loading models: {e}")
    raise
