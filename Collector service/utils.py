import os
from dotenv import load_dotenv
import httpx

def load_env():
    load_dotenv()
    return {
        "MAPBOX_TOKEN": os.getenv("MAPBOX_TOKEN"),
        "OPENWEATHER_API_KEY": os.getenv("OPENWEATHER_API_KEY"),
        "EVENTBRITE_TOKEN": os.getenv("EVENTBRITE_TOKEN"),
        "CALENDARIFIC_API_KEY": os.getenv("CALENDARIFIC_API_KEY"),
        "CALENDARIFIC_COUNTRY": os.getenv("CALENDARIFIC_COUNTRY", "IN"),
        "CALENDARIFIC_YEAR": os.getenv("CALENDARIFIC_YEAR", "2025"),
    }

async def http_get(url: str, params=None, headers=None, timeout: int = 15):
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(url, params=params, headers=headers)
        r.raise_for_status()
        return r.json()
