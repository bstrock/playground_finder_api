from api import app
from fastapi.testclient import TestClient
from typing import List, NoReturn
from icecream import ic


client = TestClient(app)


# TEST CONSTANTS
SITES_IN_MN = 503
CARCINOGEN_SITES_IN_MN = 267
WATER_RELEASE_SITES_IN_MN = 260
AIR_RELEASE_SITES_IN_MN = 373
CHEMICAL_SITES_IN_MN = 68
CARCINOGEN_WATER_RELEASE_SITES_IN_MN = 137

sector_tests = [
                ['Chemicals'],
                ['Chemicals', 'Food'],
                ['Chemicals', 'Food', 'Hazardous Waste']
                ]


def test_query_all() -> NoReturn:
    params = {
        "lat": 45,
        "lon": 96,
        "radius": 1000
    }

    response = client.get("/query", params=params)
    assert response.status_code == 200
    assert len(response.json()) == SITES_IN_MN


def test_query_carcinogen() -> NoReturn:

    params = {
        "lat": 45,
        "lon": 96,
        "radius": 1000,
        "carcinogen": True
    }

    response = client.get("/query", params=params)
    assert response.status_code == 200
    assert len(response.json()) == CARCINOGEN_SITES_IN_MN


def test_query_release_type(release_type: str) -> NoReturn:
    assert release_type in ["WATER", "AIR", "LAND"]

    params = {
        "lat": 45,
        "lon": 96,
        "radius": 1000,
        "release_type": release_type
    }

    response = client.get("/query", params=params)

    assert response.status_code == 200
    if release_type == "WATER":
        assert len(response.json()) == WATER_RELEASE_SITES_IN_MN
    elif release_type == "AIR":
        assert len(response.json()) == AIR_RELEASE_SITES_IN_MN


def test_spatial_query_sectors(sectors: List[str]) -> NoReturn:

    counts = []

    params = {
        "lat": 45,
        "lon": 96,
        "radius": 1000,
        "sectors": sectors
    }

    response = client.get("/query", params=params)
    assert response.status_code == 200

    total_results = len(response.json())

    if len(sectors) == 1:
        assert total_results == CHEMICAL_SITES_IN_MN
        return

    for sector in sectors:
        params = {
            "lat": 45,
            "lon": 96,
            "radius": 1000,
            "sectors": [sector]
        }

        response = client.get("/query", params=params)
        counts.append(len(response.json()))

    assert total_results == sum(counts)

def test_query_compound_carcinogen_and_release_type():

    params = {
        "lat": 45,
        "lon": 96,
        "radius": 1000,
        "carcinogen": True,
        "release_type": "WATER"
    }

    response = client.get("/query", params=params)
    assert response.status_code == 200
    assert len(response.json()) == CARCINOGEN_WATER_RELEASE_SITES_IN_MN


if __name__ == "__main__":
    # test_query_all()
    # test_query_carcinogen()
    # test_query_release_type("WATER")
    # test_query_release_type("AIR")
    for test in sector_tests:
        test_spatial_query_sectors(test)
    test_query_compound_carcinogen_and_release_type()

