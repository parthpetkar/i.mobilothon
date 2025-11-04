# collectors.py
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
# helpers
# -------------------------
def _validate_centroid(centroid: Optional[List[float]]):
    if centroid is None:
        raise ValueError("centroid missing (expected [lon, lat])")
    if not isinstance(centroid, (list, tuple)):
        raise ValueError("centroid must be a list or tuple [lon, lat]")
    if len(centroid) != 2:
        raise ValueError("centroid must contain exactly two elements: [lon, lat]")
    try:
        lon = float(centroid[0])
        lat = float(centroid[1])
    except Exception:
        raise ValueError("centroid values must be numeric")
    return lon, lat


def _normalize_categories(categories: Optional[List[str]]) -> List[str]:
    """
    Sanitize category list; return lowercased friendly tokens, deduped.
    Also unify common synonyms.
    """
    if not categories:
        return []
    out = []
    for c in categories:
        if not c or not isinstance(c, str):
            continue
        s = c.strip().lower()
        if s == "":
            continue
        # unify synonyms
        if s in ("medical store", "medical_store", "medstore"):
            s = "pharmacy"
        if s in ("grocery_store", "grocery", "grocerystore", "grocery-store"):
            s = "supermarket"
        if s in ("clinics", "clinic"):
            s = "clinic"
        out.append(s)
    seen = set()
    res = []
    for x in out:
        if x not in seen:
            seen.add(x)
            res.append(x)
    return res


# -------------------------
# Overpass query builder (supports optional category filters)
# -------------------------
OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def _build_overpass_query(
    lat: float,
    lon: float,
    radius: int = 1000,
    max_results: int = 500,
    filter_categories: Optional[List[str]] = None,
) -> str:
    """
    Build an Overpass QL query.
    - If filter_categories provided (friendly names like 'restaurant', 'cafe', 'pharmacy', 'hospital'),
      the query will include only those tags.
    - Otherwise query a broad set of keys (amenity, shop, tourism, leisure, etc.).
    """
    parts: List[str] = []
    fc = filter_categories or []

    if fc:
        mapping = {
            # Food & Beverage
            "restaurant": ("amenity", "restaurant"),
            "cafe": ("amenity", "cafe"),
            "bar": ("amenity", "bar"),
            "fast_food": ("amenity", "fast_food"),
            "pub": ("amenity", "pub"),

            # Shops
            "shop": ("shop", None),
            "mall": ("shop", "mall"),
            "supermarket": ("shop", "supermarket"),
            "market": ("shop", "market"),
            "grocery": ("shop", "supermarket"),

            # Tourism & leisure
            "hotel": ("tourism", "hotel"),
            "attraction": ("tourism", "attraction"),
            "museum": ("tourism", "museum"),
            "park": ("leisure", "park"),
            "pitch": ("leisure", "pitch"),
            "parking": ("amenity", "parking"),

            # Transport
            "bus_stop": ("public_transport", "platform"),

            # Healthcare
            "hospital": ("amenity", "hospital"),
            "clinic": ("amenity", "clinic"),
            "pharmacy": ("amenity", "pharmacy"),
            "doctors": ("amenity", "doctors"),
        }

        for cat in fc:
            if ":" in cat:
                key, val = cat.split(":", 1)
                key = key.strip()
                val = val.strip()
                parts.append(f'node["{key}"="{val}"](around:{radius},{lat},{lon});')
                parts.append(f'way["{key}"="{val}"](around:{radius},{lat},{lon});')
                parts.append(f'relation["{key}"="{val}"](around:{radius},{lat},{lon});')
                continue

            mapped = mapping.get(cat)
            if mapped:
                key, val = mapped
                if val:
                    parts.append(f'node["{key}"="{val}"](around:{radius},{lat},{lon});')
                    parts.append(f'way["{key}"="{val}"](around:{radius},{lat},{lon});')
                    parts.append(f'relation["{key}"="{val}"](around:{radius},{lat},{lon});')
                else:
                    parts.append(f'node["{key}"](around:{radius},{lat},{lon});')
                    parts.append(f'way["{key}"](around:{radius},{lat},{lon});')
                    parts.append(f'relation["{key}"](around:{radius},{lat},{lon});')
            else:
                parts.append(f'node["amenity"="{cat}"](around:{radius},{lat},{lon});')
                parts.append(f'way["amenity"="{cat}"](around:{radius},{lat},{lon});')
                parts.append(f'relation["amenity"="{cat}"](around:{radius},{lat},{lon});')

    else:
        keys = ["amenity", "shop", "tourism", "leisure", "historic", "craft", "office", "public_transport", "man_made"]
        for k in keys:
            parts.append(f'node["{k}"](around:{radius},{lat},{lon});')
            parts.append(f'way["{k}"](around:{radius},{lat},{lon});')
            parts.append(f'relation["{k}"](around:{radius},{lat},{lon});')

    q = (
        f"[out:json][timeout:25];\n"
        "(" + "\n".join(parts) + "\n);\n"
        f"out center {max_results};"
    )
    return q


# -------------------------
# Robust debug-friendly run_places_collector
# -------------------------
async def run_places_collector(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Robust Overpass places collector with validation and debug output.

    Accepts:
      - grids: optional list of {id, centroid:[lon,lat]}
      - device_location: optional [lon,lat] (used if grids empty)
      - categories: optional list of friendly names
      - radius_meters: optional int
      - max_results: optional int
      - debug: optional bool -> returns raw Overpass query and provider body
    """
    raw_grids = payload.get("grids", []) or []
    device_location = payload.get("device_location")
    radius = payload.get("radius_meters", 1000)
    max_results = payload.get("max_results", 500)
    debug = bool(payload.get("debug", False))

    # basic validation & normalization
    try:
        radius = int(radius)
        max_results = int(max_results)
        if radius <= 0 or radius > 5000:
            if radius <= 0:
                raise ValueError("radius_meters must be > 0")
            radius = min(radius, 5000)
    except Exception as e:
        return {"collector": "places", "error": f"invalid radius/max_results: {e}"}

    # device_location fallback
    if not raw_grids and device_location:
        try:
            lon, lat = _validate_centroid(device_location)
            raw_grids = [{"id": "device_location", "centroid": [lon, lat]}]
        except Exception as e:
            return {"collector": "places", "error": f"invalid device_location: {e}"}

    if not raw_grids:
        return {"collector": "places", "error": "no grids and no device_location provided"}

    provided_categories = payload.get("categories", None)
    if provided_categories is None:
        categories = ["restaurant", "cafe", "clinic", "pharmacy", "supermarket", "hospital"]
    else:
        categories = _normalize_categories(provided_categories)
        if not categories:
            categories = ["restaurant", "cafe", "clinic", "pharmacy", "supermarket", "hospital"]

    items: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=60) as client:
        for g in raw_grids:
            grid_id = g.get("id", "unknown")
            centroid = g.get("centroid")
            grid_debug = {"grid_id": grid_id}
            try:
                lon, lat = _validate_centroid(centroid)
            except Exception as e:
                msg = f"invalid centroid for grid {grid_id}: {e}"
                logger.warning(msg)
                items.append({"grid_id": grid_id, "error": msg})
                continue

            # build query and attach to debug info
            q = _build_overpass_query(lat=lat, lon=lon, radius=radius, max_results=max_results, filter_categories=categories)
            grid_debug["overpass_query"] = q

            try:
                resp = await client.post(OVERPASS_URL, data={"data": q})
            except Exception as e:
                logger.exception("HTTP request to Overpass failed for grid %s: %s", grid_id, e)
                items.append({"grid_id": grid_id, "error": f"Overpass request failed: {e}", **({"debug": grid_debug} if debug else {})})
                continue

            status = resp.status_code
            try:
                body_text = resp.text[:2000]
            except Exception:
                body_text = "<unreadable body>"

            grid_debug["provider_status"] = status
            grid_debug["provider_body_snippet"] = body_text

            if status != 200:
                logger.error("Overpass returned status %s for grid %s: %s", status, grid_id, body_text[:500])
                items.append({
                    "grid_id": grid_id,
                    "error": f"Overpass returned status {status}",
                    "provider_status": status,
                    "provider_body_snippet": body_text,
                    **({"debug": grid_debug} if debug else {})
                })
                continue

            try:
                body = resp.json()
            except Exception:
                text = resp.text
                logger.exception("Failed to parse Overpass JSON for grid %s", grid_id)
                items.append({
                    "grid_id": grid_id,
                    "error": "Overpass returned non-JSON",
                    "provider_body_snippet": body_text,
                    **({"debug": grid_debug} if debug else {})
                })
                continue

            elements = body.get("elements", [])
            if not elements:
                logger.info("Overpass returned 0 elements for grid %s (lon=%s lat=%s radius=%s)", grid_id, lon, lat, radius)
                items.append({
                    "grid_id": grid_id,
                    "centroid": [lon, lat],
                    "provider": "overpass",
                    "places_count": 0,
                    "places": [],
                    **({"debug": grid_debug, "raw_elements": elements} if debug else {})
                })
                continue

            normalized = []
            place_details = []
            for el in elements:
                if el.get("type") == "node":
                    el_lon = el.get("lon")
                    el_lat = el.get("lat")
                else:
                    center = el.get("center") or {}
                    el_lon = center.get("lon")
                    el_lat = center.get("lat")

                tags = el.get("tags") or {}
                name = tags.get("name") or tags.get("ref") or None

                category = None
                for k in ("amenity", "shop", "tourism", "leisure", "historic", "craft", "office", "public_transport", "man_made"):
                    if tags.get(k):
                        category = f"{k}:{tags.get(k)}"
                        break

                normalized_item = {
                    "osm_id": el.get("id"),
                    "osm_type": el.get("type"),
                    "name": name,
                    "category": category,
                    "tags": tags,
                    "lat": el_lat,
                    "lon": el_lon,
                }
                normalized.append(normalized_item)

                place_details.append({
                    "name": name,
                    "lat": el_lat,
                    "lon": el_lon,
                    "category": category,
                    "tags": tags
                })

            out = {
                "grid_id": grid_id,
                "centroid": [lon, lat],
                "provider": "overpass",
                "places_count": len(normalized),
                "places": normalized,
                "place_details": place_details
            }
            if debug:
                out["debug"] = grid_debug
                out["raw_elements_sample"] = elements[:10]
            items.append(out)

    return {"collector": "places", "items": items}


# -------------------------
# Geoapify routing helper (traffic)
# -------------------------
async def _geoapify_routing(lat: float, lon: float, lat2: float, lon2: float) -> Dict[str, Any]:
    api_key = cfg.get("GEOAPIFY_API_KEY")
    if not api_key:
        raise RuntimeError("GEOAPIFY_API_KEY not configured")
    url = "https://api.geoapify.com/v1/routing"
    waypoints_param = f"{lat},{lon}|{lat2},{lon2}"
    params = {
        "waypoints": waypoints_param,
        "mode": "drive",
        "apiKey": api_key,
        "details": "route_details",
        "format": "json",
    }
    logger.debug("Geoapify routing params: %s", params)
    return await http_get(url, params=params)


# -------------------------
# run_traffic_collector
# -------------------------
async def run_traffic_collector(payload: Dict[str, Any]) -> Dict[str, Any]:
    grids = payload.get("grids", []) or []
    items: List[Dict[str, Any]] = []
    for g in grids:
        grid_id = g.get("id")
        centroid = g.get("centroid")
        try:
            lon, lat = _validate_centroid(centroid)
        except Exception as e:
            logger.warning("Traffic: invalid centroid for grid %s: %s", grid_id, e)
            items.append({"grid_id": grid_id, "error": str(e)})
            continue
        lon2, lat2 = lon + 0.001, lat + 0.001
        try:
            resp = await _geoapify_routing(lat=lat, lon=lon, lat2=lat2, lon2=lon2)
            items.append({"grid_id": grid_id, "centroid": [lon, lat], "provider": "geoapify", "data": resp})
        except Exception as e:
            logger.exception("Traffic collector failed for grid %s: %s", grid_id, e)
            items.append({"grid_id": grid_id, "error": str(e)})
    return {"collector": "traffic", "items": items}


# -------------------------
# run_weather_collector
# -------------------------
async def run_weather_collector(payload: Dict[str, Any]) -> Dict[str, Any]:
    api_key = cfg.get("OPENWEATHER_API_KEY")
    if not api_key:
        return {"collector": "weather", "error": "OPENWEATHER_API_KEY not configured"}
    grids = payload.get("grids", []) or []
    tasks = []
    metas = []
    for g in grids:
        grid_id = g.get("id")
        centroid = g.get("centroid")
        try:
            lon, lat = _validate_centroid(centroid)
        except Exception as e:
            logger.warning("Weather: invalid centroid for grid %s: %s", grid_id, e)
            metas.append({"grid_id": grid_id, "error": str(e)})
            continue
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric"}
        tasks.append(http_get(url, params=params))
        metas.append({"grid_id": grid_id, "centroid": [lon, lat]})
    res = await asyncio.gather(*tasks, return_exceptions=True)
    items: List[Dict[str, Any]] = []
    for idx, meta in enumerate(metas):
        if "error" in meta:
            items.append({"grid_id": meta["grid_id"], "error": meta["error"]})
        else:
            r = res[idx]
            if isinstance(r, Exception):
                items.append({"grid_id": meta["grid_id"], "error": str(r)})
            else:
                items.append({"grid_id": meta["grid_id"], "centroid": meta["centroid"], "weather": r})
    return {"collector": "weather", "items": items}


# -------------------------
# run_events_collector
# -------------------------
async def run_events_collector(payload: Dict[str, Any]) -> Dict[str, Any]:
    eb_token = cfg.get("EVENTBRITE_TOKEN")
    cal_key = cfg.get("CALENDARIFIC_API_KEY")
    bbox = payload.get("bbox")
    city = payload.get("city")
    async def _fetch_eventbrite():
        if not eb_token:
            return {"error": "EVENTBRITE_TOKEN not configured"}
        url = "https://www.eventbriteapi.com/v3/events/search/"
        headers = {"Authorization": f"Bearer {eb_token}"}
        params = {}
        if bbox:
            params["location_bbox"] = ",".join(map(str, bbox))
        if city:
            params["location.address"] = city
        return await http_get(url, params=params, headers=headers)
    async def _fetch_calendarific():
        if not cal_key:
            return {"error": "CALENDARIFIC_API_KEY not configured"}
        url = "https://calendarific.com/api/v2/holidays"
        params = {
            "api_key": cal_key,
            "country": cfg.get("CALENDARIFIC_COUNTRY", "IN"),
            "year": cfg.get("CALENDARIFIC_YEAR", "2025"),
        }
        return await http_get(url, params=params)
    eventbrite_task = _fetch_eventbrite()
    calendarific_task = _fetch_calendarific()
    eventbrite, calendarific = await asyncio.gather(eventbrite_task, calendarific_task)
    return {
        "collector": "events",
        "eventbrite": eventbrite,
        "calendarific": calendarific,
        "metadata": {
            "city": city,
            "bbox": bbox,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }


# -------------------------
# run_grids_collector
# -------------------------
async def run_grids_collector(payload: Dict[str, Any]) -> Dict[str, Any]:
    grids = payload.get("grids", []) or []
    enriched = []
    for g in grids:
        grid_id = g.get("id")
        centroid = g.get("centroid")
        try:
            if centroid is not None:
                lon, lat = _validate_centroid(centroid)
                centroid_clean = [lon, lat]
            else:
                centroid_clean = None
        except Exception as e:
            centroid_clean = None
            logger.warning("Grid %s has invalid centroid: %s", grid_id, e)
        enriched.append(
            {
                "grid_id": grid_id,
                "validated": True,
                "centroid": centroid_clean,
                "bbox": g.get("bbox"),
                "metadata": g.get("metadata", {}),
            }
        )
    return {"collector": "grids", "items": enriched}
