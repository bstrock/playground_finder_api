import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from geoalchemy2 import shape
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, selectinload
from icecream import ic
from geojson import Feature, Polygon

from models.schemas import (
    SiteSchema,
    ReportSchema,
    ReviewSchema,
    EquipmentSchema,
    AmenitiesSchema,
    SportsFacilitiesSchema,
    UserInDBSchema,
    TokenDataSchema,
)
from models.tables import Site, User
from utils.create_spatial_db import SpatialDB

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 20000  # like two weeks


# dependencies for injection
fake_users_db = {
    "johndoe@example.com": {
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


# INJECTED DEPENDENCIES

# --CONNECTIVITY--
async def get_db():
    # dependency to provide db session
    # note that the session is called here, so using it within an endpoint follows pattern: async with Session as s
    # usually you'd see the session called in the context manager, ie: async with Session() as s
    # don't be alarmed

    s = Session()
    try:
        yield s
    finally:
        await s.close()


# --AUTHENTICATION--
def verify_password(plain_password, hashed_password):
    # the third thing that happens when we hit ./token
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    # hashes an incoming password for login or user creation
    return pwd_context.hash(password)


async def get_user(username: str):
    # the second thing that happens after we hit ./token
    # TODO:  I think this is the call to user table in db
    async with Session() as s:
        async with s.begin():
            user = await s.get(User, username)
            await s.close()
            return UserInDBSchema(**user.__dict__)


async def authenticate_user(username: str, password: str):
    # the first thing that happens when we hit ./token
    user = await get_user(username)
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
    # used to validate user credentials for authenticated endpoints
    # when a valid token is provided, returns user ID

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenDataSchema(username=username)
    except JWTError:
        raise credentials_exception
    user = await get_user(username=token_data.username)

    if user is None:
        raise credentials_exception
    return user

# -- CONVERSION --

def miles_to_meters(radius: float):
    # converts user int to meters (POSTGis Geography measurement unit)
    return radius * 1609.34


# FUNCTIONAL DEPENDENCIES
# these are not injected
def schema_to_row(schema, table):
    # unpacks Pydantic schema into corresponding table schema
    return table(**schema.dict())


async def submit_and_retrieve_site(Session, item_to_submit):
    async with Session as s:
        s.add(item_to_submit)
        site = await s.get(
            entity=Site,
            ident=item_to_submit.site_id,
            options=[
                selectinload(Site.equipment),
                selectinload(Site.amenities),
                selectinload(Site.sports_facilities),
                selectinload(Site.reviews),
                selectinload(Site.reports),
            ],
        )
        await s.commit()
    return site


async def make_site_geojson(site):
    equipment_schema = EquipmentSchema.from_orm(site.equipment[0])
    amenities_schema = AmenitiesSchema.from_orm(site.amenities[0])
    sports_facilities_schema = SportsFacilitiesSchema.from_orm(
        site.sports_facilities[0]
    )
    # geometry objects are returned as a well-known binary- we need to convert to shapely objects
    # in order to get the WKT which we can return in an http response
    geom = shape.to_shape(site.geom)
    wkt = geom.wkt
    wkt = wkt.strip("POLYGON ((").strip("))").split(" ")
    geom_tuples_list = []
    for i, coord in enumerate(wkt):
        if coord[-1] == ',':
            lat = float(coord.strip(','))
            lon = float(wkt[i-1])
            geom_tuples_list.append((lon, lat))

    geojson_properties = {
        'site_id': site.site_id,
        "site_name": site.site_name,
        "substrate_type": site.substrate_type,
        "addr_street1": site.addr_street1,
        "addr_city": site.addr_city,
        "addr_state": site.addr_state,
        "addr_zip": site.addr_zip,
        "equipment": equipment_schema.dict(),
        "amenities": amenities_schema.dict(),
        "sports_facilities": sports_facilities_schema.dict()
    }

    # sites may not have reviews or reports, so we skip these step if they don't
    if len(site.reviews) > 0:
        reviews = [ReviewSchema.from_orm(review).dict() for review in site.reviews]
        geojson_properties['reviews'] = reviews
    if len(site.reports) > 0:
        reports = [ReportSchema.from_orm(report).dict() for report in site.reports]
        geojson_properties['reports'] = reports

    site_geojson_poly = Polygon(geom_tuples_list)
    site_geojson = Feature(geometry=site_geojson_poly, properties=geojson_properties)
    return site_geojson
