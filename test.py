from api import app
from fastapi.testclient import TestClient
from icecream import ic

client = TestClient(app)

SITES_IN_MN = 503
CARCINOGEN_SITES_IN_MN = 267
WATER_RELEASE_SITES_IN_MN = 260
AIR_RELEASE_SITES_IN_MN = 373
CHEMICAL_SITES_IN_MN = 68


def test_spatial_query_all():
    params = {
        "lat": 45,
        "lon": 96,
        "radius": 1000
    }

    response = client.get("/query", params=params)
    assert response.status_code == 200
    assert len(response.json()) == SITES_IN_MN


def test_spatial_query_carcinogen():
    params = {
        "lat": 45,
        "lon": 96,
        "radius": 1000,
        "carcinogen": True
    }

    response = client.get("/query", params=params)
    assert response.status_code == 200
    assert len(response.json()) == CARCINOGEN_SITES_IN_MN


def test_spatial_query_release_type(release_type):

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


def test_spatial_query_sectors(sectors):

    counts = []

    params = {
        "lat": 45,
        "lon": 96,
        "radius": 1000,
        "sectors": sectors
    }
    ic(sectors)
    for sector in sectors:
        ic(sector)

        response = client.get("/query", params=params)
        counts.append(len(response.json()))
        ic(counts)
        ic(len(counts), sum(counts))


    params = {
        "lat": 45,
        "lon": 96,
        "radius": 1000,
        "sectors": sectors
    }

    ic(params)
    response = client.get("/query", params=params)
    ic(response.request)
    print(len(response.json()))
    assert len(response.json()) == sum(counts)


if __name__ == "__main__":
    #test_spatial_query_all()
    #test_spatial_query_carcinogen()
    #test_spatial_query_release_type("WATER")
    #test_spatial_query_release_type("AIR")
    test_spatial_query_sectors(['Chemicals'])
