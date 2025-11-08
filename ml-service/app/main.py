from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from .config import supabase, BACKEND_URL, ML_CALLBACK_SECRET
from .predictions import predict_parking_dynamics, predict_free_parking_availability
from .summary import generate_summary, generate_free_hotspots, generate_paid_parkings
from .utils import save_json_to_file
import pandas as pd
import uvicorn
import httpx
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Track processed listings to avoid duplicates
processed_listings = set()

app = FastAPI(title="ML Service - Parking Predictions", version="1.0.0")

@app.get("/predict-entire")
async def predict_entire_table():
    try:
        response = supabase.schema("parking").table("parking_features").select("*").execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="No data found")
        df = pd.DataFrame(response.data)
        predictions = predict_parking_dynamics(df)
        summary = generate_summary(predictions)
        free_hotspots = generate_free_hotspots(summary)
        paid_parkings = generate_paid_parkings(summary)
        save_json_to_file("freeHotspots.json", free_hotspots)
        save_json_to_file("paidParkings.json", paid_parkings)
        return {"status":"success", "free_hotspots_count":len(free_hotspots), "paid_parkings_count":len(paid_parkings)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/free-parking/predictions")
async def get_free_parking_predictions(
    lat: float = Query(..., description="User latitude"),
    lon: float = Query(..., description="User longitude")
):
    """
    Get free parking availability predictions near user location.
    
    Returns parking spots with availability probability and ML-computed radius
    based on predicted occupancy:
    - Low occupancy (< 0.3): 1500m radius
    - Medium occupancy (0.3-0.6): 800m radius
    - High occupancy (> 0.6): 300m radius
    """
    try:
        parking_spots = predict_free_parking_availability(lat, lon)
        
        return {
            "parking_spots": parking_spots,
            "count": len(parking_spots),
            "query": {
                "lat": lat,
                "lon": lon
            }
        }
    except Exception as e:
        logger.error(f"Error predicting free parking: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "ml-service",
        "version": "1.0.0",
        "database": "connected" if supabase else "disconnected"
    }

async def process_new_listing(parking_id: str, feature_data: dict):
    """Process a single new listing and call backend with price."""
    try:
        # Convert to DataFrame (single row)
        df = pd.DataFrame([feature_data])
        
        # Get predictions including dynamic price
        predictions = predict_parking_dynamics(df)
        if predictions.empty:
            logger.error(f"Failed to generate predictions for parking {parking_id}")
            return
        
        # Extract the predicted price
        price = float(predictions.iloc[0]['PredictedDynamicPricePerHour'])
        
        # Call backend price-callback endpoint
        async with httpx.AsyncClient(timeout=10) as client:
            callback_url = f"{BACKEND_URL.rstrip('/')}/parkings/{parking_id}/price-callback"
            headers = {
                "X-ML-Secret": ML_CALLBACK_SECRET,
                "Content-Type": "application/json"
            }
            
            logger.info(f"Calling backend callback for parking {parking_id} with price {price}")
            response = await client.post(
                callback_url,
                headers=headers,
                json={
                    "price_per_hour": float(price)  # Ensure price is float
                }
            )
            
            response_text = await response.aread()
            if response.status_code == 200:
                logger.info(f"Successfully set price {price} for parking {parking_id}")
                # Add to processed set to avoid duplicates
                processed_listings.add(parking_id)
            else:
                logger.error(f"Failed to set price for parking {parking_id}: {response.status_code} - {response_text.decode()}")
                # Log more details for debugging
                logger.error(f"Request details: URL={callback_url}, Headers={headers}, Payload={{'price_per_hour': {price}}}")
    
    except Exception as e:
        logger.error(f"Error processing parking {parking_id}: {str(e)}")

async def check_new_listings():
    """Background task to check for new listings and process them."""
    while True:
        try:
            # Query recent entries from parking_features
            response = supabase.schema("parking").table("parking_features")\
                .select("*")\
                .order('created_at', desc=True)\
                .limit(10)\
                .execute()
            
            if response.data:
                for feature in response.data:
                    # Extract parking_id from SystemCodeNumber (format: LISTING_<id>)
                    if not feature.get('SystemCodeNumber', '').startswith('LISTING_'):
                        continue
                        
                    parking_id = feature['SystemCodeNumber'].split('_')[1]
                    
                    # Skip if already processed
                    if parking_id in processed_listings:
                        continue
                    
                    logger.info(f"Processing new parking: {parking_id}")
                    await process_new_listing(parking_id, feature)
            
        except Exception as e:
            logger.error(f"Error checking new listings: {str(e)}")
        
        # Wait before next check
        await asyncio.sleep(5)  # Check every 5 seconds

@app.on_event("startup")
async def startup_event():
    """Start background task on app startup."""
    asyncio.create_task(check_new_listings())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
