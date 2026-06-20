# geo.py
from typing import Optional, Tuple


def resolve_point(lng, lat, village_lng, village_lat) -> Optional[Tuple[float, float]]:
    if lng is not None and lat is not None:
        return (float(lng), float(lat))
    if village_lng is not None and village_lat is not None:
        return (float(village_lng), float(village_lat))
    return None


def point_wkt(lng, lat) -> str:
    return f"POINT({lng} {lat})"
