from fastapi.testclient import TestClient

from ..run import app

client = TestClient(app)
import pytest


@pytest.fixture()
def params():
    return {
        "latitude": 44.85,
        "longitude": -93.47,
        "radius": 10,
    }

def test_liveness_check():
    response = client.get("/")
    assert response.status_code == 200


def test_basic_query(params):
    response = client.get("/query", params=params)
    geojson = response.json()
    assert response.status_code == 200
    assert len(geojson["features"]) == 29


def test_single_equipment_query(params):
    params["equipment"] = ["diggers"]

    response = client.get("/query", params=params)
    geojson = response.json()

    assert response.status_code == 200
    for feature in geojson["features"]:
        assert feature["properties"]["equipment"]["diggers"] > 0


def test_multiple_equipment_query(params):
    params["equipment"] = ["diggers", "musical"]

    response = client.get("/query", params=params)
    geojson = response.json()

    assert response.status_code == 200
    for feature in geojson["features"]:
        assert feature["properties"]["equipment"]["diggers"] > 0
        assert feature["properties"]["equipment"]["musical"] > 0


def test_single_amenity_query(params):
    params["amenities"] = ["splash_pad"]

    response = client.get("/query", params=params)
    geojson = response.json()

    assert response.status_code == 200
    for feature in geojson["features"]:
        assert feature["properties"]["amenities"]["splash_pad"] > 0


def test_multiple_amenities_query(params):
    params["amenities"] = ["splash_pad", "picnic_tables"]

    response = client.get("/query", params=params)
    assert response.status_code == 200
    geojson = response.json()

    for feature in geojson["features"]:
        assert feature["properties"]["amenities"]["splash_pad"] > 0
        assert feature["properties"]["amenities"]["picnic_tables"] > 0


def test_single_sports_facility_query(params):
    params["sports_facilities"] = ["baseball_diamond"]

    response = client.get("/query", params=params)
    geojson = response.json()

    assert response.status_code == 200
    for feature in geojson["features"]:
        assert feature["properties"]["sports_facilities"]["baseball_diamond"] > 0


def test_multiple_sports_facilities_query(params):
    params["sports_facilities"] = ["baseball_diamond", "soccer_field"]

    response = client.get("/query", params=params)
    geojson = response.json()

    assert response.status_code == 200
    for feature in geojson["features"]:
        assert feature["properties"]["sports_facilities"]["baseball_diamond"] > 0
        assert feature["properties"]["sports_facilities"]["soccer_field"] > 0


def test_single_compound_query(params):
    params["equipment"] = ["diggers"]
    params["amenities"] = ["splash_pad"]
    params["sports_facilities"] = ["baseball_diamond"]

    response = client.get("/query", params=params)
    assert response.status_code == 200
    geojson = response.json()

    for feature in geojson["features"]:
        assert feature["properties"]["equipment"]["diggers"] > 0
        assert feature["properties"]["amenities"]["splash_pad"] > 0
        assert feature["properties"]["sports_facilities"]["baseball_diamond"] > 0


def test_multiple_compound_query(params):
    params["equipment"] = ["diggers", "musical"]
    params["amenities"] = ["splash_pad", "picnic_tables"]
    params["sports_facilities"] = ["baseball_diamond", "soccer_field"]

    response = client.get("/query", params=params)
    geojson = response.json()

    assert response.status_code == 200
    for feature in geojson["features"]:
        assert feature["properties"]["equipment"]["diggers"] > 0
        assert feature["properties"]["equipment"]["musical"] > 0
        assert feature["properties"]["amenities"]["splash_pad"] > 0
        assert feature["properties"]["amenities"]["picnic_tables"] > 0
        assert feature["properties"]["sports_facilities"]["baseball_diamond"] > 0
        assert feature["properties"]["sports_facilities"]["soccer_field"] > 0

