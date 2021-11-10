from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Query, selectinload
from fastapi import FastAPI, Query as fastapi_Query, Depends, HTTPException, status
from datetime import datetime, timedelta

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
from api.dependencies import authenticate_user, create_access_token

# initializations
from api.routers import users

app = FastAPI()
app.include_router(users.router)


fake_users_db = {
    "johndoe@example.com": {
        "email": "1",
        "first_name": "John",
        "last_name": "Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
    }
}

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 20000  # like two weeks


# dependencies for injection


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@app.post("/token", response_model=TokenSchema)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):

    # DEPENDENCY STRUCTURE TO GET USER:
    # 1. request received
    # 2. authenticate_user calls get_user to retrieve known-good credentials from user table in db
    # 3. authenticate_user calls verify_password to compare hashes
    # 4. then we have this user here
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)

    # 4b. unless we don't...
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 5. but if we do...
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # 6. create a token
    access_token = create_access_token(
        data={
            "sub": user.email
        },  # FastAPI docs say to use sub when attaching user id to access token
        expires_delta=access_token_expires,
    )
    # 7. return the token...user can access api functions!
    return {"access_token": access_token, "token_type": "bearer"}


# it's a basic logger
logging.basicConfig(
    format="%(asctime)s %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p", level="INFO",
)


@app.get("/")
async def liveness_check():
    return

# ROUTES

'''
@app.get("/query")
async def query(
    latitude: float,
    longitude: float,
    access_token: str,
    radius: float,
    release_type: Optional[str] = None,
    carcinogen: Optional[bool] = None,
    sectors: Optional[List[str]] = fastapi_Query(None),
    Session: AsyncSession = Depends(get_db),
) -> List[SiteSchema]:
    logging.info("Query received")
    logging.info("\n\n***QUERY PARAMETERS***\n")

    # prepare PostGIS geometry object
    query_point = f"POINT({longitude} {latitude})"

    logging.info("Query point: %s", query_point)

    # build spatial query
    # note: we're using PostGIS Geography objects, which are in EPSG 4326 with meters as the unit of measure.
    query_sql = (
        Query([Site])  # must be a list
        .filter(  # refine sites by
            Site.geom.ST_DWithin(  # PostGIS function
                func.ST_GeogFromText(  # translatitudee query point to postgis geography object
                    query_point  # location searched
                ),
                radius,  # distance within which we're searching
                True,  # since we're using Geography objects, this flag enables spheroid-based calculatitudeions
            )
        )
        .options(  # this method chain allows us to specify eager loading behavior
            selectinload(  # since we're using async/session interface, loading needs to happen in query context
                Site.reports  # remember our joined inheritance structure?  this loads all joined tables.  Neat!
            )
        )
    )

    logging.debug("Query SQL: %s", str(query_sql))

    #  add filters based on optional query parameters
    if carcinogen:
        query_sql = query_sql.filter(Site.carcinogen == True)

        logging.info("Query flag: CARCINOGEN")
        logging.debug("Query SQL: %s", str(query_sql))

    if sectors:
        query_sql = query_sql.filter(Site.sector.in_(sectors))

        logging.info("Query flag: SECTORS: %s", str(sectors))
        logging.debug("Query SQL: %s", str(query_sql))

    if release_type:
        query_sql = query_sql.filter(Site.release_types.any(release_type))
        logging.info("Query flag: RELEASE TYPE: %s", str(release_type))
        logging.debug("Query SQL: %s", str(query_sql))

    logging.info("\n\n**** TRANSACTION ****\n")

    # send query to db by calling async session
    async with Session as s:
        logging.info("Transaction: BEGIN")
        async with s.begin():
            logging.info("SESSION: Checked out a connection")
            res = await s.execute(query_sql.with_session(s).statement)
            # context manager autocommits the query
            logging.info("QUERY: Submitted")
            res = res.scalars().all()  # decode results)

            sites = [
                SiteSchema.from_orm(site) for site in res
            ]  # unpack results to pydantic schema using list comprehension
        logging.info("TRANSACTION: CLOSED")

    logging.info("SESSION: returned connection to the pool")
    logging.info("\n*** END TRANSACTION ***\n")
    # db session is closed by this point

    logging.info("\n*** RESULT ***\n")

    if len(sites) == 0:
        logging.info("QUERY: NO RESULTS -- Endpoint Service COMPLETE\n\n")

    logging.info("QUERY: Results returned -- endpoint service COMPLETE\n\n")
    return sites


@app.post("/submit", response_model=ReportSchema)
async def submit(
    report: ReportSchema, Session: AsyncSession = Depends(get_db),
) -> ReportSchema:
    logging.info("Report Submission received")
    data = jsonable_encoder(report)  # it's just nice to have a dictionary

    # need to figure out which table model to base the report off of
    exclude = ["message", "site_id", "report_type"]  # common to all reports

    logging.info("Determining report type")
    for report_type in Globals.SUB_REPORTS:
        for k in data.keys():
            # each report type has a single unique column
            # we check if that column is in the report type schema, but not one of the common columns
            if (
                k in report_type.__dict__.keys()
                and k not in exclude
                and data[k] is not None
            ):  # needs all 3 conditions
                report = (
                    report_type()
                )  # we've found our report type- let's make an object
                logging.info("Linked table match: %s", report.__tablename__)
                break  # if we found the match, end the loop

    # we unpack the request submission into the report object
    logging.info("Unpacking report parameters")
    for k in data:
        if data[k] is not None:
            report.__setattr__(k, data[k])

    # send the report off to the database
    logging.info("*** TRANSACTION ***")
    async with Session as s:
        async with s.begin():
            s.add(report)

    logging.info("*** Report added successfully ***")

    # return the report back for confirmation
    logging.info("*** Returning report ***")
    return ReportSchema.from_orm(report)


@app.get("/reports")
async def get_all_reports(
    access_token: str, Session=Depends(get_db)
) -> List[ReportSchema]:
    async with Session as s:
        async with s.begin():
            stmt = select(Report)
            res = await s.execute(stmt)

    reports = res.scalars().all()

    response = [ReportSchema.from_orm(report) for report in reports]

    return response'''


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
