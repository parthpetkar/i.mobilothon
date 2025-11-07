import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx
from utils import load_env, http_get

logger = logging.getLogger("collectors")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(ch)

cfg = load_env()

# -------------------------
# Helpers
# -------------------------
def _validate_centroid(centroid: Optional[List[float]]):
    if centroid is None:
        raise ValueError("centroid missing (expected [lon, lat])")
    if not isinstance(centroid, (list, tuple)) or len(centroid) != 2:
        raise ValueError("centroid must be [lon, lat]")
    return float(centroid[0]), float(centroid[1])

# -------------------------
# Places (Parking-focused data collection)
# -------------------------
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def _normalize_categories(categories: Optional[List[str]]) -> List[str]:
    """Normalize category names for commercial places"""
    if not categories:
        return []
    mapping = {
        "medical store": "pharmacy",
        "medical_store": "pharmacy",
        "clinics": "clinic",
        "grocery": "supermarket",
        "grocery store": "supermarket"
    }
    clean = []
    for c in categories:
        if not isinstance(c, str):
            continue
        s = c.strip().lower()
        s = mapping.get(s, s)
        if s and s not in clean:
            clean.append(s)
    return clean

def _build_parking_overpass_query(lat: float, lon: float, radius: int, max_results: int) -> str:
    """Build Overpass query specifically for parking-related features"""
    # Query for all parking amenities with specific parking types
    
    q = f"""[out:json][timeout:25];
(
  // Nodes with amenity=parking
  node["amenity"="parking"](around:{radius},{lat},{lon});
  
  // Ways with amenity=parking  
  way["amenity"="parking"](around:{radius},{lat},{lon});
  
  // Relations with amenity=parking
  relation["amenity"="parking"](around:{radius},{lat},{lon});
);
out center {max_results};"""
    
    return q

def _build_commercial_overpass_query(lat: float, lon: float, radius: int, max_results: int, cats: List[str]) -> str:
    """Build Overpass query for commercial places (restaurants, cafes, etc.)"""
    mapping = {
        "restaurant": ("amenity", "restaurant"),
        "cafe": ("amenity", "cafe"),
        "hospital": ("amenity", "hospital"),
        "clinic": ("amenity", "clinic"),
        "pharmacy": ("amenity", "pharmacy"),
        "supermarket": ("shop", "supermarket"),
    }
    q_parts = []
    for cat in cats:
        key, val = mapping.get(cat, ("amenity", cat))
        q_parts.append(f'node["{key}"="{val}"](around:{radius},{lat},{lon});')
        q_parts.append(f'way["{key}"="{val}"](around:{radius},{lat},{lon});')
    q = f"[out:json][timeout:25];(\n{''.join(q_parts)});\nout center {max_results};"
    return q

async def run_places_collector(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collect places data:
    - Default (no categories): Parking-focused data from OSM
    - With categories: Commercial places (restaurants, cafes, etc.) from OSM
    """
    grids = payload.get("grids", []) or []
    radius = int(payload.get("radius_meters", 1000))
    max_results = int(payload.get("max_results", 500))
    categories = payload.get("categories")  # Check if categories are provided
    
    # Determine mode based on whether categories are provided
    is_parking_mode = categories is None or len(categories) == 0
    
    if not is_parking_mode:
        # Commercial places mode - normalize categories
        categories = _normalize_categories(categories)
    
    results = []
    async with httpx.AsyncClient(timeout=60) as client:
        for g in grids:
            gid = g.get("id")
            try:
                lon, lat = _validate_centroid(g["centroid"])
                
                if is_parking_mode:
                    # Parking mode - fetch OSM parking data
                    osm_places = []
                    q = _build_parking_overpass_query(lat, lon, radius, max_results)
                    r = await client.post(OVERPASS_URL, data={"data": q})
                    data = r.json()
                    
                    for el in data.get("elements", []):
                        if el.get("type") == "node":
                            el_lon, el_lat = el.get("lon"), el.get("lat")
                        else:
                            center = el.get("center", {})
                            el_lon, el_lat = center.get("lon"), center.get("lat")
                        
                        if el_lon is None or el_lat is None:
                            continue
                            
                        tags = el.get("tags", {})
                        parking_type = tags.get("parking", "unknown")
                        
                        osm_places.append({
                            "id": f"OSM_{el.get('id')}",  # Prefix OSM ID as specified
                            "name": tags.get("name", "Unnamed Parking"),
                            "lat": el_lat,
                            "lon": el_lon,
                            "parking_type": parking_type,
                            "source": "osm",
                            "tags": tags
                        })
                    
                    results.append({
                        "grid_id": gid, 
                        "centroid": [lon, lat],
                        "provider": "parking_osm", 
                        "places_count": len(osm_places),
                        "mode": "parking",
                        "places": osm_places
                    })
                    
                else:
                    # Commercial places mode - fetch commercial data
                    commercial_places = []
                    q = _build_commercial_overpass_query(lat, lon, radius, max_results, categories)
                    r = await client.post(OVERPASS_URL, data={"data": q})
                    data = r.json()
                    
                    for el in data.get("elements", []):
                        if el.get("type") == "node":
                            el_lon, el_lat = el.get("lon"), el.get("lat")
                        else:
                            center = el.get("center", {})
                            el_lon, el_lat = center.get("lon"), center.get("lat")
                        
                        if el_lon is None or el_lat is None:
                            continue
                            
                        tags = el.get("tags", {})
                        
                        commercial_places.append({
                            "id": el.get("id"),  # OSM ID
                            "name": tags.get("name", "Unnamed"),
                            "lat": el_lat,
                            "lon": el_lon,
                            "source": "osm",
                            "tags": tags
                        })
                    
                    results.append({
                        "grid_id": gid, 
                        "centroid": [lon, lat],
                        "provider": "commercial_osm", 
                        "places_count": len(commercial_places),
                        "mode": "commercial",
                        "categories": categories,
                        "places": commercial_places
                    })
                
            except Exception as e:
                logger.error(f"Error collecting places for grid {gid}: {str(e)}")
                results.append({"grid_id": gid, "error": str(e)})
                
    return {"collector": "places", "items": results}

# -------------------------
# Traffic (Geoapify)
# -------------------------
async def _geoapify_routing(lat, lon, lat2, lon2):
    key = cfg.get("GEOAPIFY_API_KEY")
    if not key:
        raise RuntimeError("GEOAPIFY_API_KEY missing")
    url = "https://api.geoapify.com/v1/routing"
    params = {"waypoints": f"{lat},{lon}|{lat2},{lon2}", "mode": "drive", "apiKey": key}
    return await http_get(url, params=params)

async def run_traffic_collector(payload: Dict[str, Any]) -> Dict[str, Any]:
    grids = payload.get("grids", []) or []
    out = []
    for g in grids:
        gid = g.get("id")
        try:
            lon, lat = _validate_centroid(g["centroid"])
            lon2, lat2 = lon + 0.001, lat + 0.001
            res = await _geoapify_routing(lat, lon, lat2, lon2)
            out.append({"grid_id": gid, "centroid": [lon, lat], "data": res})
        except Exception as e:
            out.append({"grid_id": gid, "error": str(e)})
    return {"collector": "traffic", "items": out}

# -------------------------
# Weather (OpenWeather)
# -------------------------
async def run_weather_collector(payload: Dict[str, Any]) -> Dict[str, Any]:
    key = cfg.get("OPENWEATHER_API_KEY")
    if not key:
        return {"collector": "weather", "error": "OPENWEATHER_API_KEY missing"}
    grids = payload.get("grids", []) or []
    tasks, meta = [], []
    for g in grids:
        gid = g["id"]
        lon, lat = _validate_centroid(g["centroid"])
        url = "https://api.openweathermap.org/data/2.5/weather"
        tasks.append(http_get(url, params={"lat": lat, "lon": lon, "appid": key, "units": "metric"}))
        meta.append({"grid_id": gid, "centroid": [lon, lat]})
    res = await asyncio.gather(*tasks, return_exceptions=True)
    out = []
    for i, m in enumerate(meta):
        r = res[i]
        if isinstance(r, Exception):
            out.append({"grid_id": m["grid_id"], "error": str(r)})
        else:
            out.append({"grid_id": m["grid_id"], "centroid": m["centroid"], "weather": r})
    return {"collector": "weather", "items": out}

# -------------------------
# Events (PredictHQ + Calendarific)
# -------------------------
async def run_events_collector(payload: Dict[str, Any]) -> Dict[str, Any]:
    phq = cfg.get("PREDICTHQ_TOKEN")
    cal = cfg.get("CALENDARIFIC_API_KEY")
    geo = cfg.get("GEOAPIFY_API_KEY")
    loc, city = payload.get("location"), payload.get("city")
    lon, lat = (loc or [None, None])[0], (loc or [None, None])[1]

    if not city and lon and lat and geo:
        try:
            rev = await http_get("https://api.geoapify.com/v1/geocode/reverse",
                                 params={"lat": lat, "lon": lon, "apiKey": geo})
            props = rev.get("features", [{}])[0].get("properties", {})
            city = props.get("city") or props.get("state")
        except Exception:
            pass

    if not city:
        return {"collector": "events", "error": "City or coordinates required for event lookup"}

    async def predicthq():
        if not phq:
            return {"error": "PREDICTHQ_TOKEN missing"}
        return await http_get("https://api.predicthq.com/v1/events/",
                              headers={"Authorization": f"Bearer {phq}"},
                              params={"country": "IN", "q": city, "limit": 20, "sort": "rank"})

    async def calendarific():
        if not cal:
            return {"error": "CALENDARIFIC_API_KEY missing"}
        return await http_get("https://calendarific.com/api/v2/holidays",
                              params={"api_key": cal, "country": cfg["CALENDARIFIC_COUNTRY"], "year": cfg["CALENDARIFIC_YEAR"]})

    phq_data, cal_data = await asyncio.gather(predicthq(), calendarific())
    events = phq_data.get("results", []) if isinstance(phq_data, dict) else []
    holidays = cal_data.get("response", {}).get("holidays", []) if isinstance(cal_data, dict) else []
    return {
        "collector": "events",
        "predictHQ": {"count": len(events), "events": events},
        "calendarific": {"count": len(holidays), "holidays": holidays},
        "metadata": {"city": city, "timestamp": datetime.utcnow().isoformat() + "Z"}
    }

# -------------------------
# Grids (Validation)
# -------------------------
async def run_grids_collector(payload: Dict[str, Any]) -> Dict[str, Any]:
    grids = payload.get("grids", []) or []
    items = []
    for g in grids:
        gid = g.get("id")
        try:
            lon, lat = _validate_centroid(g.get("centroid"))
            items.append({
                "grid_id": gid,
                "validated": True,
                "centroid": [lon, lat],
                "bbox": g.get("bbox"),
                "metadata": g.get("metadata", {})
            })
        except Exception as e:
            items.append({
                "grid_id": gid,
                "validated": False,
                "error": str(e),
                "centroid": g.get("centroid"),
                "bbox": g.get("bbox"),
                "metadata": g.get("metadata", {})
            })
    return {"collector": "grids", "count": len(items), "items": items, "timestamp": datetime.utcnow().isoformat() + "Z"}
