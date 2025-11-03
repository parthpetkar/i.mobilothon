from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from collectors import (
    run_traffic_collector,
    run_places_collector,
    run_weather_collector,
    run_events_collector,
    run_grids_collector,
)

app = FastAPI(title="Collectors API", version="1.0")

class GridCell(BaseModel):
    id: str
    centroid: List[float]  # [lon, lat]
    bbox: Optional[List[float]] = None  # [min_lon, min_lat, max_lon, max_lat]
    metadata: Dict[str, Any] = {}

class TrafficRequest(BaseModel):
    grids: List[GridCell]

class PlacesRequest(BaseModel):
    grids: List[GridCell]
    categories: Optional[List[str]] = None
    radius_meters: Optional[int] = 500

class WeatherRequest(BaseModel):
    grids: List[GridCell]

class EventsRequest(BaseModel):
    bbox: Optional[List[float]]
    city: Optional[str]

class GridsRequest(BaseModel):
    grids: List[GridCell]


@app.post("/collectors/traffic")
async def collectors_traffic(req: TrafficRequest):
    try:
        return await run_traffic_collector(req.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/collectors/places")
async def collectors_places(req: PlacesRequest):
    try:
        return await run_places_collector(req.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/collectors/weather")
async def collectors_weather(req: WeatherRequest):
    try:
        return await run_weather_collector(req.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/collectors/calender")
async def collectors_events(req: EventsRequest):
    try:
        return await run_events_collector(req.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/collectors/grids")
async def collectors_grids(req: GridsRequest):
    try:
        return await run_grids_collector(req.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
