from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from collectors import (
    run_places_collector,
    run_traffic_collector,
    run_weather_collector,
    run_events_collector,
    run_grids_collector,
)
from uvicorn import run
from transform import (
    transform_parking_data,
    prepare_for_supabase,
    save_to_supabase
)
from supabase import create_client
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase configuration (validate at startup)
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Pune city configuration
PUNE_CENTER = [73.8567, 18.5204]  # [longitude, latitude]
PUNE_BBOX = [73.7200, 18.4100, 74.0500, 18.6400]  # [min_lon, min_lat, max_lon, max_lat]
PUNE_GRIDS = [
    {
        "id": "pune_center",
        "centroid": [73.8567, 18.5204],
        "bbox": [73.8367, 18.5004, 73.8767, 18.5404],
        "metadata": {"area": "Pune Central"}
    },
    {
        "id": "pune_kothrud",
        "centroid": [73.8074, 18.5074],
        "bbox": [73.7874, 18.4874, 73.8274, 18.5274],
        "metadata": {"area": "Kothrud"}
    },
    {
        "id": "pune_koregaon_park",
        "centroid": [73.8956, 18.5362],
        "bbox": [73.8756, 18.5162, 73.9156, 18.5562],
        "metadata": {"area": "Koregaon Park"}
    },
    {
        "id": "pune_hadapsar",
        "centroid": [73.9297, 18.5089],
        "bbox": [73.9097, 18.4889, 73.9497, 18.5289],
        "metadata": {"area": "Hadapsar"}
    },
    {
        "id": "pune_hinjewadi",
        "centroid": [73.6977, 18.5912],
        "bbox": [73.6777, 18.5712, 73.7177, 18.6112],
        "metadata": {"area": "Hinjewadi IT Park"}
    }
]

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Collector & Transformer Service", version="2.0.0")

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

class TrafficReq(BaseModel): 
    grids: List[Grid]
    
class WeatherReq(BaseModel): 
    grids: List[Grid]

class EventsReq(BaseModel):
    location: Optional[List[float]] = None
    bbox: Optional[List[float]] = None
    city: Optional[str] = None

class GridsReq(BaseModel): 
    grids: List[Grid]

class TransformRequest(BaseModel):
    """Request for transformation endpoint"""
    grids: Optional[List[Grid]] = None  # Optional, defaults to Pune grids
    categories: Optional[List[str]] = None  # None = parking mode, List = commercial mode
    radius_meters: Optional[int] = 1000
    max_results: Optional[int] = 500
    save_to_supabase: Optional[bool] = True
    max_records_to_save: Optional[int] = 1000  # Limit records saved to Supabase

class TransformResponse(BaseModel):
    """Response from transformation"""
    success: bool
    message: str
    records_collected: int
    records_transformed: int
    records_saved: int
    execution_time_seconds: float

@app.get("/collectors/places")
async def collect_places(): 
    """Collect parking places data for Pune city (default mode - no categories)"""
    return await run_places_collector({
        "grids": PUNE_GRIDS,
        "radius_meters": 1000,
        "max_results": 500
    })

@app.get("/collectors/traffic")
async def collect_traffic(): 
    """Collect traffic data for Pune city"""
    return await run_traffic_collector({
        "grids": PUNE_GRIDS
    })

@app.get("/collectors/weather")
async def collect_weather(): 
    """Collect weather data for Pune city"""
    return await run_weather_collector({
        "grids": PUNE_GRIDS
    })

@app.get("/collectors/events")
async def collect_events(): 
    """Collect events data for Pune city"""
    return await run_events_collector({
        "location": PUNE_CENTER,
        "city": "Pune"
    })

@app.get("/collectors/grids")
async def collect_grids(): 
    """Get grid data for Pune city"""
    return await run_grids_collector({
        "grids": PUNE_GRIDS
    })


@app.post("/ingest/parking")
async def ingest_parking(record: dict):
    """Ingest a single parking/listing into Supabase parking_features for ML consumption.

    Expected payload keys: parking_id, name, location ( [lng, lat] ), slots, amenities, operator_id
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise HTTPException(status_code=500, detail="Supabase credentials not configured")

    # Basic validation
    parking_id = record.get("parking_id")
    location = record.get("location", []) or []
    if not parking_id or len(location) < 2:
        raise HTTPException(status_code=400, detail="parking_id and location [lng, lat] required")

    # Prepare data collection
    from datetime import datetime
    now = datetime.utcnow()
    try:
        lng = float(location[0])
        lat = float(location[1])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid location coordinates")

    # Create a grid for the parking location
    parking_grid = {
        "id": f"parking_{parking_id}",
        "centroid": [lng, lat],
        "bbox": [lng - 0.01, lat - 0.01, lng + 0.01, lat + 0.01],  # ~1km radius
        "metadata": {"area": record.get("name", "Unknown Area")}
    }

    # Collect contextual data
    logger.info(f"Collecting contextual data for parking {parking_id}")
    
    # Get traffic conditions
    traffic_data = await run_traffic_collector({"grids": [parking_grid]})
    traffic_condition = "Normal"
    if traffic_data and traffic_data.get('items'):
        traffic_item = traffic_data['items'][0]
        try:
            # Extract duration from routing response
            duration = traffic_item.get('data', {}).get('features', [])[0].get('properties', {}).get('time')
            if duration:
                duration_minutes = duration / 60
                if duration_minutes < 5:
                    traffic_condition = "Light"
                elif duration_minutes < 15:
                    traffic_condition = "Normal"
                elif duration_minutes < 30:
                    traffic_condition = "Heavy"
                else:
                    traffic_condition = "Congested"
        except (IndexError, KeyError, TypeError):
            pass

    # Get weather data
    weather_data = await run_weather_collector({"grids": [parking_grid]})
    is_special_day = 0
    if weather_data and weather_data.get('items'):
        weather_item = weather_data['items'][0]
        # Consider special weather conditions
        try:
            conditions = weather_item.get('data', {}).get('weather', [{}])[0].get('main', '').lower()
            if any(cond in conditions for cond in ['rain', 'snow', 'storm']):
                is_special_day = 1
        except (IndexError, KeyError, TypeError):
            pass

    # Get events data
    events_data = await run_events_collector({
        "location": [lng, lat],
        "city": "Pune"
    })
    # If there are events nearby, consider it a special day
    if events_data and events_data.get('items', []):
        is_special_day = 1

    # Categorize time based on hour
    def categorize_time(hour: int) -> str:
        if 5 <= hour < 12:
            return 'Morning'
        elif 12 <= hour < 17:
            return 'Afternoon'
        elif 17 <= hour < 21:
            return 'Evening'
        else:
            return 'Night'

    logger.info(f"Creating feature record with traffic={traffic_condition}, special_day={is_special_day}")
    feature = {
        "SystemCodeNumber": f"LISTING_{parking_id}",
        "Capacity": int(record.get("slots", 0)),
        "Latitude": lat,
        "Longitude": lng,
        "Occupancy": 0,
        "VehicleType": "car",
        "TrafficConditionNearby": traffic_condition,
        "QueueLength": 0,
        "IsSpecialDay": is_special_day,
        "Timestamp": now.strftime('%Y-%m-%d %H:%M:%S'),
        "Timestamp_WIB": now.strftime('%Y-%m-%d %H:%M:%S'),
        "Hour": now.hour,
        "DayOfWeek": now.weekday(),
        "DayName": now.strftime('%A'),
        "IsWeekend": 1 if now.weekday() in [5,6] else 0,
        "IsHoliday": 0,  # Could enhance with actual holiday data
        "TimeCategory": categorize_time(now.hour),
        "Duration_Minutes": 60,
        "EstimatedDuration_Minutes": 60
    }

    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        resp = supabase.schema("parking").table("parking_features").insert([feature]).execute()
        if getattr(resp, 'error', None):
            raise Exception(str(resp.error))
        return {"status": "ok", "inserted": len(resp.data or [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to insert feature: {str(e)}")

@app.post("/transform/collect-and-transform", response_model=TransformResponse)
async def collect_and_transform(req: Optional[TransformRequest] = Body(default=None)):
    """
    Collect data from all sources AND transform it into parking features.
    
    Defaults to Pune city if no grids specified.
    
    Steps:
    1. Collects data from all 5 collector endpoints
    2. Transforms collected data into ML features (using transform.py module)
    3. Optionally saves to Supabase
    """
    # Create default request if none provided
    if req is None:
        req = TransformRequest()
    
    # Convert to Grid models and use Pune grids as default
    if req.grids:
        grids = []
        for g in req.grids:
            if isinstance(g, dict):
                grid = Grid(**g)
            else:
                grid = g
            # Validate centroid format
            if not grid.centroid or len(grid.centroid) != 2:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid grid '{grid.id}': centroid must be [longitude, latitude] with exactly 2 values. Got: {grid.centroid}"
                )
            grids.append(grid)
    else:
        grids = [Grid(**g) for g in PUNE_GRIDS]
    
    start_time = datetime.now()
    logger.info("=" * 80)
    logger.info("Starting Collection & Transformation Pipeline")
    logger.info(f"Location: {'Custom grids' if req.grids else 'Pune City (default)'}")
    logger.info(f"Grids: {len(grids)}")
    logger.info("=" * 80)
    
    try:
        # Step 1: Collect data from all sources
        logger.info("Step 1: Collecting data from all sources...")
        logger.info(f"Using {len(grids)} grids")
        for i, g in enumerate(grids):
            logger.info(f"  Grid {i+1}: {g.id}, centroid={g.centroid}")
        
        # Collect places
        places_data = await run_places_collector({
            "grids": [g.model_dump() for g in grids],
            "categories": req.categories,  # None = parking mode, List = commercial mode
            "radius_meters": req.radius_meters,
            "max_results": req.max_results
        })
        
        # Collect traffic
        traffic_data = await run_traffic_collector({
            "grids": [g.model_dump() for g in grids]
        })
        
        # Collect weather
        weather_data = await run_weather_collector({
            "grids": [g.model_dump() for g in grids]
        })
        
        # Collect events
        events_data = {}
        if grids:
            centroid = grids[0].centroid
            events_data = await run_events_collector({
                "location": centroid,
                "city": "Pune"
            })
        
        logger.info(f"✓ Collected places: {len(places_data.get('items', []))} grids")
        logger.info(f"✓ Collected traffic: {len(traffic_data.get('items', []))} grids")
        logger.info(f"✓ Collected weather: {len(weather_data.get('items', []))} grids")
        
        # Step 2: Transform the collected data using transform module
        logger.info("Step 2: Transforming data using transform module...")
        
        df = transform_parking_data(
            places_data=places_data,
            traffic_data=traffic_data,
            weather_data=weather_data,
            events_data=events_data
        )
        
        if df.empty:
            logger.warning("No data collected to transform")
            return TransformResponse(
                success=False,
                message="No data collected",
                records_collected=0,
                records_transformed=0,
                records_saved=0,
                execution_time_seconds=(datetime.now() - start_time).total_seconds()
            )
        
        records_transformed = len(df)
        logger.info(f"✓ Transformed {records_transformed} records")
        
        # Step 3: Optionally save to Supabase
        records_saved = 0
        if req.save_to_supabase:
            # Use global Supabase credentials from environment
            if not SUPABASE_URL or not SUPABASE_KEY:
                logger.warning("Supabase credentials not found in environment variables")
                logger.info("Step 3: Skipping Supabase save (credentials missing)")
            else:
                logger.info("Step 3: Saving to Supabase...")
                try:
                    # Prepare records for database
                    records = prepare_for_supabase(df)
                    
                    # Log the limit
                    if req.max_records_to_save:
                        logger.info(f"Limiting save to {req.max_records_to_save} records (out of {len(records)} total)")
                    
                    # Save to Supabase with limit
                    records_saved = save_to_supabase(
                        records=records,
                        supabase_url=SUPABASE_URL,
                        supabase_key=SUPABASE_KEY,
                        max_records=req.max_records_to_save
                    )
                    
                    logger.info(f"✓ Saved {records_saved} records to Supabase")
                except Exception as e:
                    logger.error(f"Error saving to Supabase: {str(e)}")
                    # Continue even if save fails
        else:
            logger.info("Step 3: Skipping Supabase save (not requested)")
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        logger.info("=" * 80)
        logger.info("Pipeline complete!")
        logger.info(f"Execution time: {execution_time:.2f}s")
        logger.info("=" * 80)
        
        return TransformResponse(
            success=True,
            message="Collection and transformation completed successfully",
            records_collected=len(places_data.get('items', [])),
            records_transformed=records_transformed,
            records_saved=records_saved,
            execution_time_seconds=execution_time
        )
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        execution_time = (datetime.now() - start_time).total_seconds()
        
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline failed: {str(e)}"
        )

@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    """Health check endpoint"""
    try:
        # Check Supabase connection
        supabase_status = "connected" if SUPABASE_URL and SUPABASE_KEY else "disconnected"
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "collector-service",
            "version": "2.3.0",
            "database": supabase_status
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "service": "collector-service",
            "error": str(e)
        }

@app.get("/")
async def root():
    """Service info"""
    return {
        "service": "Dual-Mode Data Collector & Transformer Service",
        "version": "2.3.0",
        "location": "Pune, India",
        "description": "Intelligent data collection: Parking mode (default) or Commercial places mode (with categories)",
        "modes": {
            "parking_mode": {
                "trigger": "No categories parameter or empty categories",
                "description": "Collects parking-specific data from OSM",
                "data_source": "OpenStreetMap parking amenities"
            },
            "commercial_mode": {
                "trigger": "Categories parameter provided",
                "description": "Collects commercial places (restaurants, cafes, etc.)",
                "data_source": "OpenStreetMap commercial amenities"
            }
        },
        "endpoints": {
            "collectors": {
                "GET /collectors/places": "Collect parking places data for Pune (default: parking mode)",
                "GET /collectors/traffic": "Collect traffic data for Pune",
                "GET /collectors/weather": "Collect weather data for Pune",
                "GET /collectors/events": "Collect events data for Pune",
                "GET /collectors/grids": "Get grid data for Pune"
            },
            "transformer": {
                "POST /transform/collect-and-transform": "Collect all data and transform. Use 'categories' param to switch modes"
            }
        },
        "examples": {
            "parking_mode": {
                "request": {"grids": None, "categories": None},
                "description": "Collects parking data (default)"
            },
            "commercial_mode": {
                "request": {"grids": None, "categories": ["restaurant", "cafe", "hospital"]},
                "description": "Collects commercial places data"
            }
        },
        "pune_grids": [
            "pune_center - Central Pune",
            "pune_kothrud - Kothrud Area",
            "pune_koregaon_park - Koregaon Park",
            "pune_hadapsar - Hadapsar Area",
            "pune_hinjewadi - Hinjewadi IT Park"
        ]
    }

if __name__ == "__main__":
    run("main:app", host="127.0.0.1", port=8080, reload=True)
