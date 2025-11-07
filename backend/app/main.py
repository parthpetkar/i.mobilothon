from fastapi import FastAPI
from app.routers import parkings, bookings, seller
from app.config import SUPABASE_URL, REDIS_URL
from datetime import datetime

app = FastAPI(title="Parking Marketplace API", version="1.0.0")

app.include_router(parkings.router)
app.include_router(bookings.router)
app.include_router(seller.router)

@app.get("/")
async def root():
    return {"message": "Parking Marketplace API - MVP"}

@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check():
    """Health check endpoint supporting both GET and HEAD methods.
    
    GET - Returns health status with details
    HEAD - Quick check, returns just status code 200 if healthy
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": app.version,
        "services": {
            "database": SUPABASE_URL is not None,
            "redis": REDIS_URL is not None
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)