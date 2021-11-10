from fastapi import FastAPI
from fastapi.testclient import TestClient
from utils.playground_data_to_db import PlaygroundLoader
import geopandas as gpd
from api.main import app
from icecream import ic

client = TestClient(app)
import pytest
import asyncio
from test.test_db_schema import Session
from models.tables import Site, Equipment, Amenities, SportsFacilities, User


def test_liveness_check(startup):
    response = client.get("/")
    assert response.status_code == 200


def test_login():
    user = {
        'username': 'johndoe@example.com',
        'password': 'secret'
    }
    response = client.post('/token', data=user)
    token_data = response.json()
    assert response.status_code == 200
    assert token_data['access_token']
    assert token_data['token_type'] == 'bearer'

    return token_data


def test_create_existing_user():
    user = {
        'first_name': 'Steve',
        'last_name': 'Irwin',
        'email': 'steve@crochunter.com',
        'hashed_password': 'secret',
    }

    response = client.post('/users/create', json=user)
    assert response.status_code == 500


def test_create_new_user():
    user = {
        'first_name': "John",
        'last_name': "Doe",
        'email': 'johndoe@example.com',
        'hashed_password': 'secret'
    }

    response = client.post('/users/create', json=user)
    assert response.status_code == 200

    with Session() as s:
        with s.begin():
            presence_test = s.get(User, user['email'])
            assert presence_test
