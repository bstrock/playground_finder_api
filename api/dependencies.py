import os
from datetime import datetime, timedelta
from typing import Optional

from geoalchemy2 import shape
from geojson import Feature, Polygon
from jose import jwt
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, selectinload

from .models.schemas import (
    ReportSchema,
    ReviewSchema,
    EquipmentSchema,
    AmenitiesSchema,
    SportsFacilitiesSchema,
)
from .models.tables import Site

url = os.environ.get("SECRET_URL")
engine = create_async_engine(url=url, echo=False, future=True)
Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

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
        if coord[-1] == ",":
            lat = float(coord.strip(","))
            lon = float(wkt[i - 1])
            geom_tuples_list.append((lon, lat))

    geojson_properties = {
        "site_id": site.site_id,
        "site_name": site.site_name,
        "substrate_type": site.substrate_type,
        "addr_street1": site.addr_street1,
        "addr_city": site.addr_city,
        "addr_state": site.addr_state,
        "addr_zip": site.addr_zip,
        "equipment": equipment_schema.dict(),
        "amenities": amenities_schema.dict(),
        "sports_facilities": sports_facilities_schema.dict(),
    }

    # sites may not have reviews or reports, so we skip these step if they don't
    if len(site.reviews) > 0:
        reviews = [ReviewSchema.from_orm(review).dict() for review in site.reviews]
        geojson_properties["reviews"] = reviews
    if len(site.reports) > 0:
        reports = [ReportSchema.from_orm(report).dict() for report in site.reports]
        geojson_properties["reports"] = reports

    site_geojson_poly = Polygon(geom_tuples_list)
    site_geojson = Feature(geometry=site_geojson_poly, properties=geojson_properties)
    return site_geojson
