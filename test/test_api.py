from fastapi import FastAPI
from fastapi.testclient import TestClient
from api.main import app
from icecream import ic
client = TestClient(app)


def test_liveness_check():
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

