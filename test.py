from api import app
from fastapi.testclient import TestClient
from typing import List, NoReturn, Dict
from icecream import ic
from httpx import AsyncClient
from copy import deepcopy
from pandas import DataFrame, read_csv
import asyncio
from tri_data_to_db import TRILoader
from datetime import datetime as dt
import os

client = TestClient(app)
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")


class TestQueries:
    sector_tests = [
        ["Chemicals"],
        ["Chemicals", "Food"],
        ["Chemicals", "Food", "Transportation Equipment"],
    ]

    test_params = {
        "lat": 45,
        "lon": -96,
        "radius": 1000,
        "access_token": os.environ.get("SECRET_KEY"),
    }

    # TEST CONSTANTS
    SITES_MN = 503

    CARCINOGEN_SITES_MN = 267

    WATER_RELEASE_SITES_MN = 28
    AIR_RELEASE_SITES_MN = 321
    CARCINOGEN_AIR_RELEASE_SITES_MN = 201
    CARCINOGEN_WATER_RELEASE_SITES_MN = 20

    CHEMICAL_SITES_MN = 68
    CHEMICAL_AIR_RELEASE_SITES_MN = 52
    CARCINOGEN_CHEMICAL_AIR_RELEASE_SITES_MN = 27

    FOOD_SITES_MN = 76
    FOOD_AIR_RELEASE_SITES_MN = 28
    CARCINOGEN_FOOD_AIR_RELEASE_SITES_MN = 8

    TRANSPORTATION_EQUIPMENT_SITES_MN = 20
    TRANSPORTATION_EQUIPMENT_AIR_RELEASE_SITES_MN = 12
    CARCINOGEN_TRANSPORTATION_EQUIPMENT_AIR_RELEASE_SITES_MN = 7

    SPATIAL_TEST_10_MILE_RADIUS = 2
    SPATIAL_TEST_100_MILE_RADIUS = 100

    SPATIAL_EXPECTED_RESPONSE = [
        {
            "address": "800 DIAGONAL ST",
            "carcinogen": False,
            "chemicals": {"n-Hexane": {"total": 189178.05, "unit": "Pounds"}},
            "city": "DAWSON",
            "latitude": 44.93265,
            "longitude": 44.93265,
            "name": "AG PROCESSING INC A COOPERATIVE",
            "release_types": ["AIR"],
            "reports": [],
            "sector": "Food",
            "site_id": "56232GPRCS8THDI",
            "state": "MN",
            "total_releases": 189178.05,
            "zip": 56232,
        },
        {
            "address": "HWY 212 & COUNTY RD 25",
            "carcinogen": True,
            "chemicals": {
                "Copper compounds": {"total": 0.0, "unit": "Pounds"},
                "Formaldehyde": {"total": 0.0, "unit": "Pounds"},
                "Methanol": {"total": 0.0, "unit": "Pounds"},
            },
            "city": "DAWSON",
            "latitude": 44.936564,
            "longitude": 44.936564,
            "name": "JENNIE-O TURKEYSTORE DAWSON FEED MILL",
            "release_types": [None],
            "reports": [],
            "sector": "Food",
            "site_id": "56232LNDLKHWY21",
            "state": "MN",
            "total_releases": 0.0,
            "zip": 56232,
        },
    ]

    @staticmethod
    def test_release_type(df: DataFrame, release_type: str) -> NoReturn:

        types = df.release_types.apply(
            lambda x: True if release_type in x else False
        )  # true if cell contains release type
        value_set = set(
            types
        )  # can contain either True or False values, needs to contain only True

        assert len(value_set) == 1  # TEST: only one type of boolean value is present
        check = value_set.pop()  # the value present
        assert check == True  # TEST: the only value present is True

    @staticmethod
    async def test_query_all() -> NoReturn:
        # TEST CASE:  Spatial query which selects all sites in MN

        params = deepcopy(TestQueries.test_params)

        async with AsyncClient(app=app, base_url="http://localhost:8000") as ac:
            response = await ac.get("/query", params=params)

        assert response.status_code == 200
        ic(len(response.json()))
        assert len(response.json()) == TestQueries.SITES_MN

        for site in response.json():
            if site["site_id"] == TestSubmit.test_params["site_id"]:
                ic(site)

    @staticmethod
    async def test_query_carcinogen() -> NoReturn:
        # TEST CASE:  Spatial query which selects all carcinogen sites in MN

        params = deepcopy(TestQueries.test_params)
        params["carcinogen"] = True
        async with AsyncClient(app=app, base_url="http://localhost:8000") as ac:
            response = await ac.get("/query", params=params)

        df = DataFrame(response.json())

        assert (
            len(response.json()) == TestQueries.CARCINOGEN_SITES_MN
        )  # TEST:  returns correct # of results
        assert (df.carcinogen.unique()) == [
            True
        ]  # TEST: ensure all results are carcinogen

    @staticmethod
    async def test_query_release_type(release_type: str) -> NoReturn:
        # TEST CASE: Spatial query which selects sites in MN based on release type

        params = deepcopy(TestQueries.test_params)
        params["release_type"] = release_type
        # response = client.get("/query", params=params)

        async with AsyncClient(app=app, base_url="http://localhost:8000") as ac:
            response = await ac.get("/query", params=params)

        assert response.status_code == 200

        # TEST: ensure all results contain the desired result type
        df = DataFrame(response.json())

        # check for presence of release_type in result
        TestQueries.test_release_type(df=df, release_type=release_type)

        # TEST: query returns expected number of results
        if release_type == "WATER":
            assert len(response.json()) == TestQueries.WATER_RELEASE_SITES_MN
        elif release_type == "AIR":
            assert len(response.json()) == TestQueries.AIR_RELEASE_SITES_MN

    @staticmethod
    async def test_query_sectors(sectors: List[str]) -> NoReturn:
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
        params = deepcopy(TestQueries.test_params)
        params["sectors"] = sectors

        # full_query_response = client.get("/query", params=params)
        async with AsyncClient(app=app, base_url="http://localhost:8000") as ac:
            full_query_response = await ac.get("/query", params=params)

        assert full_query_response.status_code == 200

        res = full_query_response.json()
        df = DataFrame(res)
        total_results = len(res)

        # TEST: ensure supplied and returned sectors match
        # this test will fail if provided with zero-result sector query
        # this test case is out of scope for testing- if results are correct when all sectors return at least 1 result,
        # it will also work if some of the sectors queried are 0

        # without sorting, alphabetical order of list items produces false negative
        sectors_received = df.sector.unique().tolist().sort()
        assert sectors_received == sectors.sort()

        if len(sectors) == 1:
            assert total_results == TestQueries.CHEMICAL_SITES_MN
            return  # no need to check sum total when there's only one sector

        # record results returned by queries for individual sectors
        for sector in sectors:
            params["sectors"] = [sector]
            # response = client.get("/query", params=params)

            async with AsyncClient(app=app, base_url="http://localhost:8000") as ac:
                response = await ac.get("/query", params=params)

            counts.append(len(response.json()))

        assert total_results == sum(counts)

        if len(sectors) == 2:
            assert total_results == TestQueries.CHEMICAL_SITES_MN + TestQueries.FOOD_SITES_MN
        elif len(sectors) == 3:
            assert (
                total_results
                == TestQueries.CHEMICAL_SITES_MN + TestQueries.FOOD_SITES_MN + TestQueries.TRANSPORTATION_EQUIPMENT_SITES_MN
            )

    @staticmethod
    async def test_query_compound_carcinogen_and_release_type(
        release_type: str,
    ) -> NoReturn:
        # TEST CASE:
        # Compound spatial query which selects carcinogen sites in MN based on release type

        params = deepcopy(TestQueries.test_params)
        params["carcinogen"] = True
        params["release_type"] = release_type

        # response = client.get("/query", params=params)
        async with AsyncClient(app=app, base_url="http://localhost:8000") as ac:
            response = await ac.get("/query", params=params)

        assert response.status_code == 200
        res = response.json()
        df = DataFrame(res)

        assert (df.carcinogen.unique()) == [
            True
        ]  # TEST: ensure all results are carcinogen

        TestQueries.test_release_type(df=df, release_type=release_type)

        if release_type == "WATER":
            assert len(res) == TestQueries.CARCINOGEN_WATER_RELEASE_SITES_MN
        elif release_type == "AIR":
            assert len(res) == TestQueries.CARCINOGEN_AIR_RELEASE_SITES_MN

    @staticmethod
    async def test_query_compound_carcinogen_and_release_type_and_sectors(
        sectors: List[str], release_type: str, carcinogen: bool
    ) -> NoReturn:
        # TEST CASE:
        # Compound spatial query which selects carcinogen sites in MN based on release type and sector

        params = deepcopy(TestQueries.test_params)
        counts = []

        if carcinogen:
            params["carcinogen"] = True
        params["release_type"] = release_type
        params["sectors"] = sectors

        # query_all_response = client.get("/query", params=params)
        async with AsyncClient(app=app, base_url="http://localhost:8000") as ac:
            query_all_response = await ac.get("/query", params=params)

        assert query_all_response.status_code == 200

        res = query_all_response.json()
        df = DataFrame(res)

        TestQueries.test_release_type(df, release_type)

        total_results = len(res)

        if len(sectors) == 1:
            if carcinogen:
                assert (df.carcinogen.unique()) == [
                    True
                ]  # TEST: ensure all results are carcinogen
                assert total_results == TestQueries.CARCINOGEN_CHEMICAL_AIR_RELEASE_SITES_MN
            else:
                assert total_results == TestQueries.CHEMICAL_AIR_RELEASE_SITES_MN
            return

        for sector in sectors:
            params["sectors"] = [sector]
            # response = client.get("/query", params=params)
            async with AsyncClient(app=app, base_url="http://localhost:8000") as ac:
                response = await ac.get("/query", params=params)

            counts.append(len(response.json()))

        assert total_results == sum(counts)

        if len(sectors) == 2:
            if carcinogen:

                assert (df.carcinogen.unique()) == [
                    True
                ]  # TEST: ensure all results are carcinogen
                assert (
                    total_results
                    == TestQueries.CARCINOGEN_CHEMICAL_AIR_RELEASE_SITES_MN
                    + TestQueries.CARCINOGEN_FOOD_AIR_RELEASE_SITES_MN
                )
            else:
                assert (
                    total_results
                    == TestQueries.CHEMICAL_AIR_RELEASE_SITES_MN + TestQueries.FOOD_AIR_RELEASE_SITES_MN
                )

        elif len(sectors) == 3:
            if carcinogen:
                assert (df.carcinogen.unique()) == [
                    True
                ]  # TEST: ensure all results are carcinogen
                assert (
                    total_results
                    == TestQueries.CARCINOGEN_CHEMICAL_AIR_RELEASE_SITES_MN
                    + TestQueries.CARCINOGEN_FOOD_AIR_RELEASE_SITES_MN
                    + TestQueries.CARCINOGEN_TRANSPORTATION_EQUIPMENT_AIR_RELEASE_SITES_MN
                )
            else:
                assert (
                    total_results
                    == TestQueries.CHEMICAL_AIR_RELEASE_SITES_MN
                    + TestQueries.FOOD_AIR_RELEASE_SITES_MN
                    + TestQueries.TRANSPORTATION_EQUIPMENT_AIR_RELEASE_SITES_MN
                )

    @staticmethod
    async def test_spatial_query():
        params = deepcopy(TestQueries.test_params)

        for r in [10, 100]:
            params["radius"] = r
            async with AsyncClient(app=app, base_url="http://localhost:8000") as ac:
                response = await ac.get("/query", params=params)

            assert response.status_code == 200

            if r == 10:
                assert response.json() == TestQueries.SPATIAL_EXPECTED_RESPONSE
            elif r == 100:
                assert len(response.json()) == TestQueries.SPATIAL_TEST_100_MILE_RADIUS

    @staticmethod
    async def run_panel():
        await TestQueries.test_query_all()
        await TestQueries.test_query_carcinogen()
        await TestQueries.test_query_release_type(release_type="WATER")
        await TestQueries.test_query_release_type(release_type="AIR")
        await TestQueries.test_query_compound_carcinogen_and_release_type(
            release_type="WATER"
        )
        await TestQueries.test_query_compound_carcinogen_and_release_type(
            release_type="AIR"
        )

        for test_sector in TestQueries.sector_tests:
            await TestQueries.test_query_sectors(sectors=test_sector)
            await TestQueries.test_query_compound_carcinogen_and_release_type_and_sectors(
                sectors=test_sector, release_type="AIR", carcinogen=False
            )

            await TestQueries.test_query_compound_carcinogen_and_release_type_and_sectors(
                sectors=test_sector, release_type="AIR", carcinogen=True
            )

        await TestQueries.test_spatial_query()


class TestSubmit:

    test_message = "You are reading the thing which I have typed."
    test_params = {
        "site_id": "55413NTRPL2015N",
        "message": test_message,
        "access_token": os.environ.get("SECRET_KEY"),
    }

    # 55003NDRSNFOOTO

    report_params = [
        {"report_type": "Activity", "activity_type": "Sitework"},
        {"report_type": "Emission", "emission_type": "Water"},
        {"report_type": "Unused Site", "unused_type": "Signage"},
    ]

    EXPECTED_INHERITANCE_RESPONSE = [
        {
            "activity_type": None,
            "emission_type": "Water",
            "message": "You are reading the thing which I have typed.",
            "report_id": "2",
            "report_type": "Emission",
            "site_id": "55413NTRPL2015N",
            "unused_type": None,
        },
        {
            "activity_type": "Sitework",
            "emission_type": None,
            "message": "You are reading the thing which I have typed.",
            "report_id": "1",
            "report_type": "Activity",
            "site_id": "55413NTRPL2015N",
            "unused_type": None,
        },
        {
            "activity_type": None,
            "emission_type": None,
            "message": "You are reading the thing which I have typed.",
            "report_id": "3",
            "report_type": "Unused Site",
            "site_id": "55413NTRPL2015N",
            "unused_type": "Signage",
        },
    ]

    @staticmethod
    async def test_submit(report_params: Dict[str, str]) -> NoReturn:

        params = deepcopy(TestSubmit.test_params)
        params = {**params, **report_params}

        async with AsyncClient(app=app, base_url="http://localhost:8000") as ac:
            response = await ac.post("/submit", json=params)

        assert response.status_code == 200
        res = response.json()

        expected = {k: v for k, v in params.items() if v is not None}
        generated_keys = ["timestamp", "report_id", "access_token"]
        for k in expected:
            if k not in generated_keys:

                assert k in res.keys()
                assert res[k] == expected[k]

    @staticmethod
    async def test_inheritance():
        async with AsyncClient(app=app, base_url="http://localhost:8000") as ac:
            response = await ac.get(
                "/reports", params={"access_token": os.environ.get("SECRET_KEY")}
            )

        assert response.status_code == 200
        assert response.json() == TestSubmit.EXPECTED_INHERITANCE_RESPONSE

    @staticmethod
    async def run_panel():
        for report in TestSubmit.report_params:
            await TestSubmit.test_submit(report)
        await TestSubmit.test_inheritance()


if __name__ == "__main__":
    start = dt.now()
    data = read_csv("~/Downloads/tri_20_mn.csv")  # this is a dataframe
    tri_loader = TRILoader()  # set loader class
    tri_loader.set_data(data=data)  # load data

    asyncio.run(
        tri_loader.main()
    )  # run protocols to create db and tables, then import the dataframe

    async def main():
        await asyncio.wait(
            [TestSubmit.run_panel(), TestQueries.run_panel()]
        )  # run protocols to create db and tables, then import the dataframeTestQueries.run_panel()  # run the query tests

    asyncio.run(main())
    end = dt.now()

    delta = end - start
    ic(delta.total_seconds())
    # requests.post("http://0.0.0.0:8001/submit", json=json.dumps(TestSubmit.test_params))
