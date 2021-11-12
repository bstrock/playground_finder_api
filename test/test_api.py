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


@pytest.fixture()
def params():
    return {
        'latitude': 44.85,
        'longitude': -93.47,
        'radius': 1000,
    }


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
    assert response.status_code == 403


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


def test_basic_query(params):
    response = client.get('/query', params=params)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_single_equipment_query(params):
    params['equipment'] = ['diggers']

    response = client.get('/query', params=params)
    assert response.status_code == 200
    inventory = response.json()
    for site in inventory:
        assert site['equipment']['diggers'] > 0


def test_multiple_equipment_query(params):
    params['equipment'] = ['diggers', 'musical']

    response = client.get('/query', params=params)
    assert response.status_code == 200
    inventory = response.json()
    for site in inventory:
        assert site['equipment']['diggers'] > 0
        assert site['equipment']['musical'] > 0


def test_single_amenity_query(params):
    params['amenities'] = ['splash_pad']

    response = client.get('/query', params=params)
    assert response.status_code == 200
    inventory = response.json()
    for site in inventory:
        assert site['amenities']['splash_pad'] > 0


def test_multiple_amenities_query(params):
    params['amenities'] = ['splash_pad', 'picnic_tables']

    response = client.get('/query', params=params)
    assert response.status_code == 200
    inventory = response.json()
    for site in inventory:
        assert site['amenities']['splash_pad'] > 0
        assert site['amenities']['picnic_tables'] > 0


def test_single_sports_facility_query(params):
    params['sports_facilities'] = ['baseball_diamond']

    response = client.get('/query', params=params)
    assert response.status_code == 200
    inventory = response.json()
    for site in inventory:
        assert site['sports_facilities']['baseball_diamond'] > 0


def test_multiple_sports_facilities_query(params):
    params['sports_facilities'] = ['baseball_diamond', 'soccer_field']

    response = client.get('/query', params=params)
    assert response.status_code == 200
    inventory = response.json()
    for site in inventory:
        assert site['sports_facilities']['baseball_diamond'] > 0
        assert site['sports_facilities']['soccer_field'] > 0


def test_single_compound_query(params):
    params['equipment'] = ['diggers']
    params['amenities'] = ['splash_pad']
    params['sports_facilities'] = ['baseball_diamond']

    response = client.get('/query', params=params)
    assert response.status_code == 200
    inventory = response.json()
    for site in inventory:
        assert site['equipment']['diggers'] > 0
        assert site['amenities']['splash_pad'] > 0
        assert site['sports_facilities']['baseball_diamond'] > 0


def test_multiple_compound_query(params):
    params['equipment'] = ['diggers', 'musical']
    params['amenities'] = ['splash_pad', 'picnic_tables']
    params['sports_facilities'] = ['baseball_diamond', 'soccer_field']

    response = client.get('/query', params=params)
    assert response.status_code == 200
    inventory = response.json()
    for site in inventory:
        assert site['equipment']['diggers'] > 0
        assert site['equipment']['musical'] > 0
        assert site['amenities']['splash_pad'] > 0
        assert site['amenities']['picnic_tables'] > 0
        assert site['sports_facilities']['baseball_diamond'] > 0
        assert site['sports_facilities']['soccer_field'] > 0
