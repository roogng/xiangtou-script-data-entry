# tests/test_geo.py
from geo import resolve_point, point_wkt


def test_uses_kimi_coords_when_present():
    assert resolve_point(120.1, 30.2, village_lng=119.0, village_lat=29.0) == (120.1, 30.2)


def test_falls_back_to_village_coords():
    assert resolve_point(None, None, village_lng=119.0, village_lat=29.0) == (119.0, 29.0)


def test_returns_none_when_nothing():
    assert resolve_point(None, None, village_lng=None, village_lat=None) is None


def test_point_wkt_format():
    assert point_wkt(120.1, 30.2) == "POINT(120.1 30.2)"
