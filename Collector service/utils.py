# utils.py
import os
import logging
from dotenv import load_dotenv
import httpx
from typing import Optional, Dict, Any

# simple logger
logger = logging.getLogger("utils")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(ch)


def load_env() -> Dict[str, Optional[str]]:
    """
    Load environment variables from .env and return a dict of relevant keys.
    """
    load_dotenv()
    return {
        "GEOAPIFY_API_KEY": os.getenv("GEOAPIFY_API_KEY"),
        "OPENWEATHER_API_KEY": os.getenv("OPENWEATHER_API_KEY"),
        "EVENTBRITE_TOKEN": os.getenv("EVENTBRITE_TOKEN"),
        "CALENDARIFIC_API_KEY": os.getenv("CALENDARIFIC_API_KEY"),
        "CALENDARIFIC_COUNTRY": os.getenv("CALENDARIFIC_COUNTRY", "IN"),
        "CALENDARIFIC_YEAR": os.getenv("CALENDARIFIC_YEAR", "2025"),
        "TRAVELTIME_APP_ID": os.getenv("TRAVELTIME_APP_ID"),
        "TRAVELTIME_API_KEY": os.getenv("TRAVELTIME_API_KEY"),
    }


async def http_get(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 20
) -> Any:
    """
    Async GET helper using httpx.
    - Raises httpx.HTTPStatusError for non-2xx responses.
    - Logs provider response snippet for debugging.
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            try:
                return resp.json()
            except Exception:
                text = resp.text
                logger.warning("http_get: non-JSON response from %s (len=%d)", url, len(text))
                return {"_raw_text": text}
    except httpx.HTTPStatusError as e:
        body = ""
        try:
            body = e.response.text
        except Exception:
            pass
        logger.error("HTTPStatusError fetching %s: %s -- resp: %s", url, str(e), body[:1000])
        raise
    except Exception as e:
        logger.exception("Error fetching %s: %s", url, e)
        raise
