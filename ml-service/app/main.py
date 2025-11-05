from fastapi import FastAPI, HTTPException
from .config import supabase
from .predictions import predict_parking_dynamics
from .summary import generate_summary, generate_free_hotspots, generate_paid_parkings
from .utils import save_json_to_file
import pandas as pd
import uvicorn

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

@app.get("/health")
async def health():
    return {"status":"healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
