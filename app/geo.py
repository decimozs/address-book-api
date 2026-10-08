"""Geographic helpers."""
import math

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in kilometres."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = phi2 - phi1
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def bounding_box(lat: float, lon: float, radius_km: float) -> tuple[float, float, float, float]:
    """Return (min_lat, max_lat, min_lon, max_lon) enclosing the search circle.

    Used as a cheap SQL pre-filter before the exact haversine check. Near the
    poles or the antimeridian the longitude range is widened to the full span.
    """
    d_lat = math.degrees(radius_km / EARTH_RADIUS_KM)
    min_lat, max_lat = lat - d_lat, lat + d_lat
    if min_lat <= -90 or max_lat >= 90:
        return max(min_lat, -90), min(max_lat, 90), -180.0, 180.0
    d_lon = math.degrees(radius_km / (EARTH_RADIUS_KM * math.cos(math.radians(lat))))
    min_lon, max_lon = lon - d_lon, lon + d_lon
    if min_lon < -180 or max_lon > 180:
        return min_lat, max_lat, -180.0, 180.0
    return min_lat, max_lat, min_lon, max_lon
