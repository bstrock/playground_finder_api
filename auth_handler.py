# app/auth/auth_handler.py

import time
from typing import Dict

import jwt



JWT_SECRET = config("secret")
JWT_ALGORITHM = config("algorithm")


def token_response(token: str):
    return {
        "access_token": token
    }