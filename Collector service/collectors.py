from utils import load_env, http_get
from typing import Dict, Any, List
import asyncio
import logging

logger = logging.getLogger("collectors")

cfg = load_env()


# -------------------------
# Mapbox Places Helper
# -------------------------
async def mapbox_place_search(lon: float, lat: float, categories: List[str], radius: int):
    token = cfg.get("MAPBOX_TOKEN")
    base = "https://api.mapbox.com/geocoding/v5/mapbox.places"
    
    # Enhanced category mapping for better search results
    search_queries = {
        "mall": ["shopping mall", "mall in Bengaluru"],
        "restaurant": ["restaurants near", "food"],
        "cafe": ["cafe", "coffee shop"],
        "park": ["park", "garden"],
        "commercial": ["commercial area", "business district"],
        "market": ["market", "shopping area"]
    }
    
    # Search for each category
    all_results = []
    for category in categories:
        queries = search_queries.get(category, [category])
        for query in queries:
            # Add location context to the search
            search_term = f"{query}"
            url = f"{base}/{search_term}.json"
            
            params = {
                "access_token": token,
                "proximity": f"{lon},{lat}",
                "bbox": f"{lon-0.1},{lat-0.1},{lon+0.1},{lat+0.1}",  # Wider area
                "limit": 10,
                "types": "poi,place",
                "language": "en"
            }
            
            try:
                result = await http_get(url, params=params)
                if result and "features" in result:
                    # Process and enhance each feature
                    for feature in result["features"]:
                        if feature.get("place_type") and feature.get("text"):
                            feature["properties"] = feature.get("properties", {})
                            feature["properties"].update({
                                "name": feature.get("text"),
                                "category": category,
                                "address": feature.get("place_name", ""),
                                "distance": feature.get("distance", 0),
                                "relevance": feature.get("relevance", 1.0),
                                "place_type": feature.get("place_type")[0]
                            })
                            all_results.append(feature)
            except Exception as e:
                logger.error(f"Error searching for {category} - {query}: {str(e)}")
                continue
        
        try:
            result = await http_get(base, params=params)
            if result and "suggestions" in result:
                # Convert Searchbox API response to GeoJSON format
                features = []
                for suggestion in result["suggestions"]:
                    if suggestion.get("name"):  # Only include results with names
                        feature = {
                            "type": "Feature",
                            "id": suggestion.get("mapbox_id"),
                            "geometry": {
                                "type": "Point",
                                "coordinates": suggestion.get("coordinates", [lon, lat])
                            },
                            "properties": {
                                "name": suggestion.get("name"),
                                "category": category,
                                "address": suggestion.get("full_address", ""),
                                "distance": suggestion.get("distance_meters"),
                                "place_type": suggestion.get("place_type", ["poi"])[0],
                                "relevance": suggestion.get("relevance", 1.0)
                            }
                        }
                        features.append(feature)
                all_results.extend(features)
        except Exception as e:
            logger.error(f"Error searching for category {category}: {str(e)}")
            continue
    
    # Deduplicate results based on place ID
    seen_ids = set()
    unique_features = []
    for feature in all_results:
        if feature.get("id") not in seen_ids:
            seen_ids.add(feature.get("id"))
            unique_features.append(feature)
    
    return {
        "type": "FeatureCollection",
        "features": unique_features,
        "query": [f"{lon},{lat}"],
        "attribution": "NOTICE: © 2025 Mapbox and its suppliers. All rights reserved. Use of this data is subject to the Mapbox Terms of Service (https://www.mapbox.com/about/maps/)."
    }


# -------------------------
# Collector: Traffic (Mapbox)
# -------------------------
async def run_traffic_collector(payload: dict) -> dict:
    token = cfg.get("MAPBOX_TOKEN")
    results = []
    grids = payload.get("grids", [])
    import httpx

    for g in grids:
        centroid = g.get("centroid")
        if not centroid:
            continue
        lon, lat = centroid
        coords = f"{lon},{lat};{lon+0.001},{lat+0.001}"
        url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{coords}"
        params = {
            "access_token": token,
            "geometries": "geojson",
            "overview": "simplified",
            "annotations": "duration,distance,speed",
        }
        async with httpx.AsyncClient() as client:
            r = await client.get(url, params=params, timeout=20)
            data = r.json()
        results.append({"grid_id": g.get("id"), "centroid": centroid, "data": data})

    return {"collector": "traffic", "items": results}


# -------------------------
# Collector: Places (Mapbox)
# -------------------------
async def run_places_collector(payload: dict) -> dict:
    grids = payload.get("grids", [])
    categories = payload.get("categories") or ["poi"]  # Default to POI if no categories
    radius = payload.get("radius_meters", 2000)  # Increased default radius
    
    # Enhanced search categories
    category_mapping = {
        "shop": ["retail", "store", "supermarket", "shopping"],
        "mall": ["mall", "shopping center", "shopping mall"],
        "market": ["market", "marketplace", "bazaar", "commercial"],
        "commercial": ["business", "office", "commercial", "corporate"],
        "office": ["office building", "business center", "corporate"],
        "poi": ["point of interest", "landmark", "attraction"]
    }
    
    expanded_categories = []
    for cat in categories:
        if cat in category_mapping:
            expanded_categories.extend(category_mapping[cat])
        else:
            expanded_categories.append(cat)
    
    tasks = []
    for g in grids:
        if g.get("centroid"):
            lon, lat = g["centroid"]
            # Make multiple searches with different terms for better coverage
            for category in expanded_categories:
                tasks.append(mapbox_place_search(lon, lat, [category], radius))
    
    all_results = await asyncio.gather(*tasks, return_exceptions=True)
    items = []
    
    for idx, grid in enumerate(grids):
        if not grid.get("centroid"):
            continue
            
        grid_results = []
        grid_start_idx = idx * len(expanded_categories)
        grid_end_idx = (idx + 1) * len(expanded_categories)
        
        # Combine results for this grid
        for r in all_results[grid_start_idx:grid_end_idx]:
            if not isinstance(r, Exception) and r.get("features"):
                grid_results.extend(r["features"])
        
        # Remove duplicates based on place ID
        seen_places = set()
        unique_places = []
        for place in grid_results:
            place_id = place.get("id")
            if place_id and place_id not in seen_places:
                seen_places.add(place_id)
                unique_places.append(place)
        
        # Create response for this grid with detailed place information
        place_details = []
        for place in unique_places:
            properties = place.get("properties", {})
            coordinates = place.get("geometry", {}).get("coordinates", [])
            place_details.append({
                "name": properties.get("name", "Unnamed"),
                "category": properties.get("category", "other"),
                "address": properties.get("address", ""),
                "coordinates": coordinates,
                "distance": properties.get("distance", "N/A"),
                "place_type": properties.get("type", ""),
                "relevance": properties.get("relevance", 1.0)
            })

        grid_response = {
            "grid_id": grid.get("id"),
            "places": {
                "type": "FeatureCollection",
                "features": unique_places,
                "query": [f"{grid['centroid'][0]},{grid['centroid'][1]}"],
                "attribution": "NOTICE: © 2025 Mapbox and its suppliers. All rights reserved."
            },
            "place_details": sorted(place_details, key=lambda x: x["relevance"], reverse=True),
            "count": len(unique_places),
            "summary": {
                "total_places": len(unique_places),
                "location_types": {},
                "categories_searched": expanded_categories,
                "place_names": [p["name"] for p in place_details if p["name"] != "Unnamed"]
            }
        }
        
        # Categorize places
        for place in unique_places:
            place_type = place.get("properties", {}).get("category", "other")
            grid_response["summary"]["location_types"][place_type] = \
                grid_response["summary"]["location_types"].get(place_type, 0) + 1
        
        items.append(grid_response)
    
    return {
        "collector": "places",
        "items": items
    }


# -------------------------
# Collector: Weather (OpenWeatherMap)
# -------------------------
async def run_weather_collector(payload: dict) -> dict:
    api_key = cfg.get("OPENWEATHER_API_KEY")
    grids = payload.get("grids", [])
    tasks = []
    for g in grids:
        if g.get("centroid"):
            lon, lat = g["centroid"]
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric"}
            tasks.append(http_get(url, params=params))
    res = await asyncio.gather(*tasks, return_exceptions=True)
    items = []
    for idx, r in enumerate(res):
        if isinstance(r, Exception):
            items.append({"grid_id": grids[idx].get("id"), "error": str(r)})
        else:
            items.append({"grid_id": grids[idx].get("id"), "weather": r})
    return {"collector": "weather", "items": items}


# -------------------------
# Collector: Events (Eventbrite + Calendarific)
# -------------------------
async def run_events_collector(payload: dict) -> dict:
    eb_token = cfg.get("EVENTBRITE_TOKEN")
    cal_key = cfg.get("CALENDARIFIC_API_KEY")
    bbox = payload.get("bbox")
    city = payload.get("city", "Bengaluru")

    async def fetch_calendarific():
        url = "https://calendarific.com/api/v2/holidays"
        params = {
            "api_key": cal_key,
            "country": cfg.get("CALENDARIFIC_COUNTRY", "IN"),
            "year": cfg.get("CALENDARIFIC_YEAR", "2025"),
            "type": "national,local,religious"
        }
        try:
            return await http_get(url, params=params)
        except Exception as e:
            logger.error(f"Calendarific API error: {str(e)}")
            return {"holidays": [], "error": str(e)}

    calendarific_result = (await asyncio.gather(fetch_calendarific()))[0]  # Get first item from list
    
    return {
        "collector": "events",
        "calendarific": calendarific_result,
        "metadata": {
            "city": city,
            "bbox": bbox,
            "timestamp": "2025-11-03T06:55:22Z",  # Current timestamp
            "apis": {
                "calendarific": bool(calendarific_result.get("response", {}).get("holidays", []))
            }
        }
    }


# -------------------------
# Collector: Grids
# -------------------------
async def run_grids_collector(payload: dict) -> dict:
    grids = payload.get("grids", [])
    enriched = [
        {
            "grid_id": g.get("id"),
            "validated": True,
            "centroid": g.get("centroid"),
            "bbox": g.get("bbox"),
            "metadata": g.get("metadata", {}),
        }
        for g in grids
    ]
    return {"collector": "grids", "items": enriched}
