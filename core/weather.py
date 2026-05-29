import requests
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def check_historical_weather(lat: float, lon: float, date_str: str) -> Dict[str, Any]:
    """
    Check historical weather using Open-Meteo free API to validate visual weather conditions.
    date_str format: YYYY-MM-DD
    """
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": date_str,
        "end_date": date_str,
        "daily": "temperature_2m_mean,precipitation_sum,snowfall_sum",
        "timezone": "auto"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            daily = data.get("daily", {})
            return {
                "temperature": daily.get("temperature_2m_mean", [None])[0],
                "precipitation": daily.get("precipitation_sum", [None])[0],
                "snowfall": daily.get("snowfall_sum", [None])[0]
            }
        else:
            logger.warning(f"Weather API returned {response.status_code}")
            return {}
    except Exception as e:
        logger.error(f"Weather check failed: {e}")
        return {}
