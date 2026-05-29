import math
from datetime import datetime, timezone
from astral.sun import sun
from astral import LocationInfo
import logging

logger = logging.getLogger(__name__)

def estimate_latitude(ratio_height_shadow: float, timestamp: str, longitude: float = 37.6173) -> float:
    """
    Estimate latitude based on the ratio of object height to shadow length and the time of observation.

    ratio_height_shadow: Object height / Shadow length
    timestamp: ISO 8601 string (e.g. "2023-05-12T12:00:00Z")
    longitude: Fallback longitude (default Moscow)
    """
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        # The observed altitude angle of the sun
        # tan(altitude) = height / shadow_length
        observed_altitude = math.degrees(math.atan(ratio_height_shadow))

        # We need to find the latitude where the sun's altitude matches the observed altitude at this time.
        # We'll do a simple sweep across latitudes to find the closest match.
        best_lat = 0.0
        min_diff = 90.0

        for lat_int in range(-900, 901):
            lat = lat_int / 10.0
            loc = LocationInfo(latitude=lat, longitude=longitude)
            # astral doesn't give direct altitude for a specific time easily without elevation module
            # We can use astral's elevation function
            from astral.sun import elevation
            alt = elevation(loc.observer, dt)

            diff = abs(alt - observed_altitude)
            if diff < min_diff:
                min_diff = diff
                best_lat = lat

        return best_lat
    except Exception as e:
        logger.error(f"Chronolocation failed: {e}")
        return 0.0
