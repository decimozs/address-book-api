import pytest

from app.geo import bounding_box, haversine_km


def test_haversine_known_distance():
    # London -> Paris is roughly 344 km
    assert haversine_km(51.5074, -0.1278, 48.8566, 2.3522) == pytest.approx(344, abs=2)


def test_haversine_same_point_is_zero():
    assert haversine_km(10, 10, 10, 10) == 0


def test_bounding_box_near_antimeridian_spans_all_longitudes():
    _, _, min_lon, max_lon = bounding_box(0, 179.9, 100)
    assert (min_lon, max_lon) == (-180.0, 180.0)


def test_bounding_box_near_pole_spans_all_longitudes():
    min_lat, max_lat, min_lon, max_lon = bounding_box(89.9, 10, 50)
    assert max_lat == 90
    assert (min_lon, max_lon) == (-180.0, 180.0)


def test_bounding_box_normal_case_is_tight():
    min_lat, max_lat, min_lon, max_lon = bounding_box(14.6, 121.0, 10)
    assert min_lat < 14.6 < max_lat
    assert min_lon < 121.0 < max_lon
    assert max_lat - min_lat < 0.25
