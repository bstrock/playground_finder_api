from api import app
from fastapi.testclient import TestClient
from typing import List, NoReturn
from icecream import ic
from copy import deepcopy

client = TestClient(app)


# TEST CONSTANTS
SITES_MN = 503
CARCINOGEN_SITES_MN = 267
WATER_RELEASE_SITES_MN = 260
AIR_RELEASE_SITES_MN = 373
CHEMICAL_SITES_MN = 68
CHEMICAL_AND_FOOD_SITES_MN = 144
CHEMICAL_AND_FOOD_AND_HAZARDOUS_WASTE_SITES_MN = 146
CARCINOGEN_WATER_RELEASE_SITES_MN = 137
CARCINOGEN_CHEMICAL_WATER_RELEASE_SITES_MN = 13
CARCINOGEN_CHEMICAL_AND_FOOD_WATER_RELEASE_SITES_MN = 21
CARCINOGEN_CHEMICAL_AND_FOOD_AND_HAZARDOUS_WASTE_WATER_RELEASE_SITES_MN = 22

sector_tests = [
                ['Chemicals'],
                ['Chemicals', 'Food'],
                ['Chemicals', 'Food', 'Hazardous Waste']
                ]

test_params = {
    "lat": 45,
    "lon": 96,
    "radius": 1000
}


def test_query_all() -> NoReturn:
    # TEST CASE:  Spatial query which selects all sites in MN

    params = deepcopy(test_params)
    response = client.get("/query", params=params)

    assert response.status_code == 200
    assert len(response.json()) == SITES_MN


def test_query_carcinogen() -> NoReturn:
    # TEST CASE:  Spatial query which selects all carcinogen sites in MN

    params = deepcopy(test_params)
    params["carcinogen"] = True
    response = client.get("/query", params=params)

    assert response.status_code == 200
    assert len(response.json()) == CARCINOGEN_SITES_MN


def test_query_release_type(release_type: str) -> NoReturn:
    # TEST CASE: Spatial query which selects sites in MN based on release type

    params = deepcopy(test_params)
    params["release_type"] = release_type
    response = client.get("/query", params=params)

    assert response.status_code == 200

    if release_type == "WATER":
        assert len(response.json()) == WATER_RELEASE_SITES_MN

    elif release_type == "AIR":
        assert len(response.json()) == AIR_RELEASE_SITES_MN


def test_spatial_query_sectors(sectors: List[str]) -> NoReturn:
    # TEST CASE:
    #   Spatial query which selects sites in MN based on industry sector
    #
    # METHODOLOGY:
    #   - The query can have multiple selections for industry.
    #   - Each site can have one industry.
    #   - The query is intended to return a union of all selected industries.
    #   - Each test round will check a list of 1, 2, or 3 sectors.
    #   - The function checks the cumulative total for the specified sectors, then queries each sector individually.
    #   - The cumulative total is then checked against the sum of the individual queries.

    counts = []
    params = deepcopy(test_params)
    params["sectors"] = sectors

    response = client.get("/query", params=params)
    assert response.status_code == 200

    total_results = len(response.json())

    if len(sectors) == 1:
        assert total_results == CHEMICAL_SITES_MN
        return  # no need to check sum total when there's only one sector

    for sector in sectors:
        params["sectors"] = [sector]
        response = client.get("/query", params=params)
        counts.append(len(response.json()))

    if len(sectors) == 2:
        assert total_results == sum(counts) == CHEMICAL_AND_FOOD_SITES_MN
    elif len(sectors) == 3:
        assert total_results == sum(counts) == CHEMICAL_AND_FOOD_AND_HAZARDOUS_WASTE_SITES_MN


def test_query_compound_carcinogen_and_release_type() -> NoReturn:
    params = deepcopy(test_params)
    params["carcinogen"] = True
    params["release_type"] = "WATER"

    response = client.get("/query", params=params)

    assert response.status_code == 200
    assert len(response.json()) == CARCINOGEN_WATER_RELEASE_SITES_MN


def test_query_compound_carcinogen_and_release_type_and_sectors(sectors: List[str]):
    params = deepcopy(test_params)
    counts = []

    params["carcinogen"] = True
    params["release_type"] = "WATER"
    params["sectors"] = sectors

    response = client.get("/query", params=params)
    assert response.status_code == 200

    total_results = len(response.json())

    if len(sectors) == 1:
        assert total_results == CARCINOGEN_CHEMICAL_WATER_RELEASE_SITES_MN
        return

    for sector in sectors:
        params['sectors'] = [sector]
        response = client.get("/query", params=params)
        counts.append(len(response.json()))

    if len(sectors) == 2:
        assert total_results == sum(counts) == CARCINOGEN_CHEMICAL_AND_FOOD_WATER_RELEASE_SITES_MN
    elif len(sectors) == 3:
        assert total_results == sum(counts) == CARCINOGEN_CHEMICAL_AND_FOOD_AND_HAZARDOUS_WASTE_WATER_RELEASE_SITES_MN


if __name__ == "__main__":
    test_query_all()
    test_query_carcinogen()
    test_query_release_type(release_type="WATER")
    test_query_release_type(release_type="AIR")
    test_query_compound_carcinogen_and_release_type()

    for test_sector in sector_tests:
        test_spatial_query_sectors(sectors=test_sector)
        test_query_compound_carcinogen_and_release_type_and_sectors(sectors=test_sector)
