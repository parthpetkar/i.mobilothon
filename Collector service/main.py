from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from collectors import (
    run_places_collector,
    run_traffic_collector,
    run_weather_collector,
    run_events_collector,
    run_grids_collector,
)

app = FastAPI(title="Collector Service", version="1.0.0")

class Grid(BaseModel):
    id: str
    centroid: List[float]
    bbox: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = {}

class PlacesReq(BaseModel):
    grids: List[Grid]
    categories: Optional[List[str]] = None
    radius_meters: Optional[int] = 1000
    max_results: Optional[int] = 500

class TrafficReq(BaseModel): grids: List[Grid]
class WeatherReq(BaseModel): grids: List[Grid]
class EventsReq(BaseModel):
    location: Optional[List[float]] = None
    bbox: Optional[List[float]] = None
    city: Optional[str] = None
class GridsReq(BaseModel): grids: List[Grid]

@app.post("/collectors/places")
async def collect_places(req: PlacesReq): return await run_places_collector(req.dict())
@app.post("/collectors/traffic")
async def collect_traffic(req: TrafficReq): return await run_traffic_collector(req.dict())
@app.post("/collectors/weather")
async def collect_weather(req: WeatherReq): return await run_weather_collector(req.dict())
@app.post("/collectors/events")
async def collect_events(req: EventsReq): return await run_events_collector(req.dict())
@app.post("/collectors/grids")
async def collect_grids(req: GridsReq): return await run_grids_collector(req.dict())
