from api import app
from fastapi.testclient import TestClient
from typing import List, NoReturn, Dict
from icecream import ic
from copy import deepcopy
from pandas import DataFrame

client = TestClient(app)

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


class TestQueries:
    sector_tests = [
        ['Chemicals'],
        ['Chemicals', 'Food'],
        ['Chemicals', 'Food', 'Transportation Equipment']
    ]

    test_params = {
        "lat": 45,
        "lon": 96,
        "radius": 1000
    }

    @staticmethod
    def test_release_type(df: DataFrame,
                          release_type: str
                          ) -> NoReturn:

        types = df.release_types.apply(
            lambda x: True if release_type in x else False)  # true if cell contains release type
        value_set = set(types)  # can contain either True or False values, needs to contain only True

        assert len(value_set) == 1  # TEST: only one type of boolean value is present
        check = value_set.pop()  # the value present
        assert check == True  # TEST: the only value present is True

    @staticmethod
    def test_query_all() -> NoReturn:
        # TEST CASE:  Spatial query which selects all sites in MN

        params = deepcopy(TestQueries.test_params)
        response = client.get("/query", params=params)

        assert response.status_code == 200
        assert len(response.json()) == SITES_MN

    @staticmethod
    def test_query_carcinogen() -> NoReturn:
        # TEST CASE:  Spatial query which selects all carcinogen sites in MN

        params = deepcopy(TestQueries.test_params)
        params["carcinogen"] = True
        response = client.get("/query", params=params)

        assert response.status_code == 200

        df = DataFrame(response.json())

        assert len(response.json()) == CARCINOGEN_SITES_MN  # TEST:  returns correct # of results
        assert (df.carcinogen.unique()) == [True]  # TEST: ensure all results are carcinogen

    @staticmethod
    def test_query_release_type(release_type: str) -> NoReturn:
        # TEST CASE: Spatial query which selects sites in MN based on release type

        params = deepcopy(TestQueries.test_params)
        params["release_type"] = release_type
        response = client.get("/query", params=params)

        assert response.status_code == 200

        # TEST: ensure all results contain the desired result type
        df = DataFrame(response.json())

        # check for presence of release_type in result
        TestQueries.test_release_type(df=df, release_type=release_type)

        # TEST: query returns expected number of results
        if release_type == "WATER":
            assert len(response.json()) == WATER_RELEASE_SITES_MN
        elif release_type == "AIR":
            assert len(response.json()) == AIR_RELEASE_SITES_MN

    @staticmethod
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
        params = deepcopy(TestQueries.test_params)
        params["sectors"] = sectors

        full_query_response = client.get("/query", params=params)

        assert full_query_response.status_code == 200

        res = full_query_response.json()
        df = DataFrame(res)
        total_results = len(res)

        # TEST: ensure supplied and returned sectors match
        # this test will fail if provided with zero-result sector query
        # this test case is out of scope for testing- if results are correct when all sectors return at least 1 result,
        # it will also work if some of the sectors queried are 0

        # without sorting, alphabetical order of list items produces false negative
        assert df['sector'].unique().tolist().sort() == sectors.sort()

        if len(sectors) == 1:
            assert total_results == CHEMICAL_SITES_MN
            return  # no need to check sum total when there's only one sector

        # record results returned by queries for individual sectors
        for sector in sectors:
            params["sectors"] = [sector]
            response = client.get("/query", params=params)
            counts.append(len(response.json()))

        assert total_results == sum(counts)

        if len(sectors) == 2:
            assert total_results == CHEMICAL_SITES_MN + FOOD_SITES_MN
        elif len(sectors) == 3:
            assert total_results == CHEMICAL_SITES_MN + FOOD_SITES_MN + TRANSPORTATION_EQUIPMENT_SITES_MN

    @staticmethod
    def test_query_compound_carcinogen_and_release_type(release_type: str) -> NoReturn:
        # TEST CASE:
        # Compound spatial query which selects carcinogen sites in MN based on release type

        params = deepcopy(TestQueries.test_params)
        params["carcinogen"] = True
        params["release_type"] = release_type

        response = client.get("/query", params=params)

        assert response.status_code == 200
        res = response.json()
        df = DataFrame(res)

        assert (df.carcinogen.unique()) == [True]  # TEST: ensure all results are carcinogen

        TestQueries.test_release_type(df=df, release_type=release_type)

        if release_type == "WATER":
            assert len(res) == CARCINOGEN_WATER_RELEASE_SITES_MN
        elif release_type == "AIR":
            assert len(res) == CARCINOGEN_AIR_RELEASE_SITES_MN

    @staticmethod
    def test_query_compound_carcinogen_and_release_type_and_sectors(sectors: List[str],
                                                                    release_type: str,
                                                                    carcinogen: bool
                                                                    ) -> NoReturn:
        # TEST CASE:
        # Compound spatial query which selects carcinogen sites in MN based on release type and sector

        params = deepcopy(TestQueries.test_params)
        counts = []

        if carcinogen:
            params["carcinogen"] = True
        params["release_type"] = release_type
        params["sectors"] = sectors

        query_all_response = client.get("/query", params=params)
        assert query_all_response.status_code == 200

        res = query_all_response.json()
        df = DataFrame(res)

        TestQueries.test_release_type(df, release_type)

        total_results = len(res)

        if len(sectors) == 1:
            if carcinogen:
                assert (df.carcinogen.unique()) == [True]  # TEST: ensure all results are carcinogen
                assert total_results == CARCINOGEN_CHEMICAL_AIR_RELEASE_SITES_MN
            else:
                assert total_results == CHEMICAL_AIR_RELEASE_SITES_MN
            return

        for sector in sectors:
            params['sectors'] = [sector]
            response = client.get("/query", params=params)
            counts.append(len(response.json()))

        assert total_results == sum(counts)

        if len(sectors) == 2:
            if carcinogen:
                ic(total_results)
                assert (df.carcinogen.unique()) == [True]  # TEST: ensure all results are carcinogen
                assert total_results == CARCINOGEN_CHEMICAL_AIR_RELEASE_SITES_MN + CARCINOGEN_FOOD_AIR_RELEASE_SITES_MN
            else:
                assert total_results == CHEMICAL_AIR_RELEASE_SITES_MN + FOOD_AIR_RELEASE_SITES_MN

        elif len(sectors) == 3:
            if carcinogen:
                assert (df.carcinogen.unique()) == [True]  # TEST: ensure all results are carcinogen
                assert total_results == CARCINOGEN_CHEMICAL_AIR_RELEASE_SITES_MN + CARCINOGEN_FOOD_AIR_RELEASE_SITES_MN + CARCINOGEN_TRANSPORTATION_EQUIPMENT_AIR_RELEASE_SITES_MN
            else:
                assert total_results == CHEMICAL_AIR_RELEASE_SITES_MN + FOOD_AIR_RELEASE_SITES_MN + TRANSPORTATION_EQUIPMENT_AIR_RELEASE_SITES_MN

    @staticmethod
    def run_panel():
        TestQueries.test_query_all()
        TestQueries.test_query_carcinogen()
        TestQueries.test_query_release_type(release_type="WATER")
        TestQueries.test_query_release_type(release_type="AIR")
        TestQueries.test_query_compound_carcinogen_and_release_type(release_type="WATER")
        TestQueries.test_query_compound_carcinogen_and_release_type(release_type="AIR")

        for test_sector in TestQueries.sector_tests:
            TestQueries.test_spatial_query_sectors(sectors=test_sector)
            TestQueries.test_query_compound_carcinogen_and_release_type_and_sectors(sectors=test_sector,
                                                                                    release_type="AIR",
                                                                                    carcinogen=False
                                                                                    )

            TestQueries.test_query_compound_carcinogen_and_release_type_and_sectors(sectors=test_sector,
                                                                                    release_type="AIR",
                                                                                    carcinogen=True
                                                                                    )


class TestSubmit:

    test_message = "You are reading the thing which I have typed."
    test_params = {
                   "site_id": "55003NDRSNFOOTO",
                   "message": test_message
                  }

    report_params = [
                        {
                          "report_type": "Activity",
                          "activity_type": "Sitework"
                        },
                        {
                          "report_type": "Emission",
                          "emission_type": "Water"
                        },
                        {
                          "report_type": "Unused Site",
                          "unused_type": "Signage"
                        }
                    ]

    @staticmethod
    def test_submit(report_params: Dict[str, str]) -> NoReturn:

        params = deepcopy(TestSubmit.test_params)
        params = {**params, **report_params}

        response = client.post("/submit", json=params)

        assert response.status_code == 200
        res = response.json()

        expected = {k: v for k, v in params.items() if v is not None}

        for k in expected:
            assert k in res.keys()
            assert res[k] == expected[k]


    @staticmethod
    def run_panel():
        for report in TestSubmit.report_params:
            TestSubmit.test_submit(report)

        target_site = {
                       "release_type": "AIR",
                       "carcinogen": True,
                       "sectors": "Wood Products"
                       }

        query_params = deepcopy(TestQueries.test_params)
        params = {**query_params, **target_site}
        response = client.get("/query", params=params)
        target_site_response = response.json()[3]




if __name__ == "__main__":
    pass
    #TestQueries.run_panel()
    TestSubmit.run_panel()
    #requests.post("http://0.0.0.0:8001/submit", json=json.dumps(TestSubmit.test_params))
