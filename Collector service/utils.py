import os
from dotenv import load_dotenv
import httpx
from typing import Optional, Dict, Any

def load_env() -> Dict[str, Optional[str]]:
    load_dotenv()
    return {
        "GEOAPIFY_API_KEY": os.getenv("GEOAPIFY_API_KEY"),
        "OPENWEATHER_API_KEY": os.getenv("OPENWEATHER_API_KEY"),
        "PREDICTHQ_TOKEN": os.getenv("PREDICTHQ_TOKEN"),
        "CALENDARIFIC_API_KEY": os.getenv("CALENDARIFIC_API_KEY"),
        "CALENDARIFIC_COUNTRY": os.getenv("CALENDARIFIC_COUNTRY", "IN"),
        "CALENDARIFIC_YEAR": os.getenv("CALENDARIFIC_YEAR", "2025"),
    }

async def http_get(url: str, params=None, headers=None, timeout: int = 25) -> Any:
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(url, params=params, headers=headers)
        r.raise_for_status()
        return r.json()
