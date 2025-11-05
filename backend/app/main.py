from fastapi import FastAPI
from app.routers import parkings, bookings, seller
from app.config import SUPABASE_URL, REDIS_URL

app = FastAPI(title="Parking Marketplace API", version="1.0.0")

app.include_router(parkings.router)
app.include_router(bookings.router)
app.include_router(seller.router)

@app.get("/")
async def root():
    return {"message": "Parking Marketplace API - MVP"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)