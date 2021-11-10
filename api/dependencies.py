from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Query, selectinload
from fastapi import FastAPI, Query as fastapi_Query, Depends, HTTPException, status
from datetime import datetime, timedelta
from icecream import ic
from models.schemas import (
    SiteSchema,
    ReportSchema,
    ReviewSchema,
    EquipmentSchema,
    AmenitiesSchema,
    SportsFacilitiesSchema,
    UserSchema,
    UserInDBSchema,
    TokenSchema,
    TokenDataSchema,
)

from icecream import ic
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.encoders import jsonable_encoder
from utils.create_spatial_db import SpatialDB
from models.tables import Site, Report
from typing import Optional, List
from sqlalchemy import select
from geoalchemy2 import func
import logging
import uvicorn
import os

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 20000  # like two weeks


# dependencies for injection
fake_users_db = {
    "johndoe@example.com": {
        "email": "1",
        "first_name": "John",
        "last_name": "Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
    }
}
engine = create_async_engine(url=SpatialDB.url, echo=False, future=True)
Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    # the third thing that happens when we hit ./token
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db: dict, username: str):
    # the second thing that happens after we hit ./token
    # TODO:  I think this is the call to user table in db
    if username in db:
        user_dict = db[username]
        return UserInDBSchema(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    # the first thing that happens when we hit ./token
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    # copy the data to local scope variable
    to_encode = data.copy()

    # attach expiration to token (default 15 min)
    expire = (
        datetime.utcnow() + expires_delta
        if expires_delta
        else datetime.utcnow() + timedelta(minutes=15)
    )
    to_encode.update({"exp": expire})

    # encode the token using the secret key and the user credentials/expiration
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        ic(token)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        ic(payload)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenDataSchema(username=username)
        ic(token_data)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)

    if user is None:
        raise credentials_exception
    return user

def schema_to_row(schema, table):
    return table(**schema.dict())

async def get_db():
    s = Session()
    try:
        yield s
    finally:
        await s.close()