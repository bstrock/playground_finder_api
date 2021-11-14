from fastapi import FastAPI
from fastapi.testclient import TestClient
from utils.playground_data_to_db import PlaygroundLoader
import geopandas as gpd
from api.main import app
from icecream import ic
from sqlalchemy.orm import Query

client = TestClient(app)
import pytest
import asyncio
from test.test_db_schema import Session
from models.tables import (
    Site,
    Equipment,
    Amenities,
    SportsFacilities,
    User,
    Report,
    Review,
)


@pytest.fixture()
def params():
    return {
        "latitude": 44.85,
        "longitude": -93.47,
        "radius": 100000,
    }


def test_liveness_check(startup):
    response = client.get("/")
    assert response.status_code == 200


def test_create_existing_user():
    user = {
        "first_name": "Steve",
        "last_name": "Irwin",
        "email": "steve@crochunter.com",
        "hashed_password": "secret",
    }

    response = client.post("/users/create", json=user)
    assert response.status_code == 403


def test_create_new_user():
    user = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "johndoe@example.com",
        "hashed_password": "secret",
    }

    response = client.post("/users/create", json=user)
    assert response.status_code == 200

    with Session() as s:
        with s.begin():
            presence_test = s.get(User, user["email"])
            assert presence_test


def test_login():
    user = {"username": "johndoe@example.com", "password": "secret"}
    response = client.post("/token", data=user)
    token_data = response.json()
    assert response.status_code == 200
    assert token_data["access_token"]
    assert token_data["token_type"] == "bearer"
    return token_data


def test_basic_query(params):
    response = client.get("/query", params=params)
    assert response.status_code == 200
    assert len(response.json()) == 29


def test_single_equipment_query(params):
    params["equipment"] = ["diggers"]

    response = client.get("/query", params=params)
    inventory = response.json()

    assert response.status_code == 200
    for site in inventory:
        assert site["equipment"]["diggers"] > 0


def test_multiple_equipment_query(params):
    params["equipment"] = ["diggers", "musical"]

    response = client.get("/query", params=params)
    inventory = response.json()

    assert response.status_code == 200
    for site in inventory:
        assert site["equipment"]["diggers"] > 0
        assert site["equipment"]["musical"] > 0


def test_single_amenity_query(params):
    params["amenities"] = ["splash_pad"]

    response = client.get("/query", params=params)
    inventory = response.json()

    assert response.status_code == 200
    for site in inventory:
        assert site["amenities"]["splash_pad"] > 0


def test_multiple_amenities_query(params):
    params["amenities"] = ["splash_pad", "picnic_tables"]

    response = client.get("/query", params=params)
    assert response.status_code == 200
    inventory = response.json()

    for site in inventory:
        assert site["amenities"]["splash_pad"] > 0
        assert site["amenities"]["picnic_tables"] > 0


def test_single_sports_facility_query(params):
    params["sports_facilities"] = ["baseball_diamond"]

    response = client.get("/query", params=params)
    inventory = response.json()

    assert response.status_code == 200
    for site in inventory:
        assert site["sports_facilities"]["baseball_diamond"] > 0


def test_multiple_sports_facilities_query(params):
    params["sports_facilities"] = ["baseball_diamond", "soccer_field"]

    response = client.get("/query", params=params)
    inventory = response.json()

    assert response.status_code == 200
    for site in inventory:
        assert site["sports_facilities"]["baseball_diamond"] > 0
        assert site["sports_facilities"]["soccer_field"] > 0


def test_single_compound_query(params):
    params["equipment"] = ["diggers"]
    params["amenities"] = ["splash_pad"]
    params["sports_facilities"] = ["baseball_diamond"]

    response = client.get("/query", params=params)
    assert response.status_code == 200
    inventory = response.json()

    for site in inventory:
        assert site["equipment"]["diggers"] > 0
        assert site["amenities"]["splash_pad"] > 0
        assert site["sports_facilities"]["baseball_diamond"] > 0


def test_multiple_compound_query(params):
    params["equipment"] = ["diggers", "musical"]
    params["amenities"] = ["splash_pad", "picnic_tables"]
    params["sports_facilities"] = ["baseball_diamond", "soccer_field"]

    response = client.get("/query", params=params)
    inventory = response.json()

    assert response.status_code == 200
    for site in inventory:
        assert site["equipment"]["diggers"] > 0
        assert site["equipment"]["musical"] > 0
        assert site["amenities"]["splash_pad"] > 0
        assert site["amenities"]["picnic_tables"] > 0
        assert site["sports_facilities"]["baseball_diamond"] > 0
        assert site["sports_facilities"]["soccer_field"] > 0


def test_submit_review_without_login():
    review = {
        "site_id": "S001",
        "user_email": "steve@crochunter.com",
        "stars": 4,
        "comment": "What a lovely playground!  We had the best time!",
    }

    response = client.post("/submit/review", json=review)
    status = response.json()

    assert response.status_code == 401


def test_submit_report_without_login():
    report = {
        "site_id": "S002",
        "user_email": "steve@crochunter.com",
        "report_type": "HAZARD",
        "comment": "There appears to be a giant pit in the ground next to the swings.  I feel like someone could fall in there.",
    }

    response = client.post("submit/report", json=report)
    status = response.json()

    assert response.status_code == 401


def test_submit_review_with_login():
    review = {
        "site_id": "S001",
        "user_email": "steve@crochunter.com",
        "stars": 4,
        "comment": "What a lovely playground!  We had the best time!",
    }

    token_data = test_login()
    access_token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.post("/submit/review", json=review, headers=headers)
    status = response.json()

    with Session() as s:
        with s.begin():
            query = Query([Review]).filter(Review.site_id == review["site_id"])
            res = s.execute(query.with_session(s).statement)

    for result in res.scalars().all():
        assert result.comment == review["comment"]

    assert response.status_code == 200
    assert status["site_id"] == review["site_id"]


def test_submit_report_with_login():
    report = {
        "site_id": "S002",
        "report_type": "HAZARD",
        "comment": "There appears to be a giant pit in the ground next to the swings.  I feel like someone could fall in there.",
    }

    token_data = test_login()
    access_token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.post("submit/report", json=report, headers=headers)
    status = response.json()

    with Session() as s:
        with s.begin():
            query = Query([Report]).where(Report.site_id == report["site_id"])
            res = s.execute(query.with_session(s).statement)

    for result in res.scalars().all():
        assert result.comment == report["comment"]

    assert response.status_code == 200
    assert status["site_id"] == report["site_id"]


def test_add_first_favorite_with_login():
    params = {"site_id": "S001", "operation": "add"}

    token_data = test_login()
    access_token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.post("users/me/favorites", params=params, headers=headers)
    user = response.json()

    with Session() as s:
        with s.begin():
            res = s.get(User, "johndoe@example.com")
            assert "S001" in res.favorite_parks

    assert response.status_code == 200
    assert "S001" in user["favorites"]


def test_add_second_favorite_with_login():
    params = {"site_id": "S002", "operation": "add"}

    token_data = test_login()
    access_token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.post("users/me/favorites", params=params, headers=headers)
    user = response.json()

    with Session() as s:
        with s.begin():
            res = s.get(User, "johndoe@example.com")
            assert "S001" in res.favorite_parks
            assert "S002" in res.favorite_parks

    assert response.status_code == 200
    assert "S001" in user["favorites"]
    assert "S002" in user["favorites"]


def test_remove_favorite_with_login():
    params = {"site_id": "S002", "operation": "remove"}

    token_data = test_login()
    access_token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    response = client.post("users/me/favorites", params=params, headers=headers)
    user = response.json()

    with Session() as s:
        with s.begin():
            res = s.get(User, "johndoe@example.com")
            assert "S001" in res.favorite_parks
            assert "S002" not in res.favorite_parks

    assert response.status_code == 200
    assert "S001" in user["favorites"]
    assert "S002" not in user["favorites"]
