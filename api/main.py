from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Query, selectinload
from fastapi import FastAPI, Query as fastapi_Query, Depends, HTTPException, status
from datetime import datetime, timedelta
from api.dependencies import get_db, make_site_schema_response
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
from models.tables import Review
from icecream import ic
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.encoders import jsonable_encoder
from utils.create_spatial_db import SpatialDB
from models.tables import Site, Report
from typing import Optional, List
from sqlalchemy import select
from geoalchemy2 import func, shape
import logging
import uvicorn
import os
from api.dependencies import authenticate_user, create_access_token, get_current_user

# initializations
from api.routers import users, submit

app = FastAPI()
app.include_router(users.router)
app.include_router(submit.router)

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

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


#  THIS ENDPOINT ISSUES AUTHENTICATION TOKENS FOR USERS IN THE DATABASE
@app.post("/token", response_model=TokenSchema)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # DEPENDENCY STRUCTURE TO GET USER:
    # 1. request received
    # 2. authenticate_user calls get_user to retrieve known-good credentials from user table in db
    # 3. authenticate_user calls verify_password to compare hashes
    # 4. then we have this user here
    user = await authenticate_user(form_data.username, form_data.password)

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


# THIS ENDPOINT IS USED IN TESTING TO ESTABLISH FUNCTIONALITY AND TRIGGER DB STARTUP/TEARDOWN PROCEDURE
# PUBLIC ENDPOINT
@app.get("/")
async def liveness_check():
    return


# THIS ENDPOINT IS USED TO QUERY PARKS NEAR THE USER
# PUBLIC ENDPOINT
@app.get("/query")
async def query(
    latitude: float,
    longitude: float,
    radius: float,
    equipment: Optional[List[str]] = fastapi_Query(None),
    amenities: Optional[List[str]] = fastapi_Query(None),
    sports_facilities: Optional[List[str]] = fastapi_Query(None),
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
                func.ST_GeogFromText(  # translate query point to postgis geography object
                    query_point  # location searched
                ),
                radius,  # distance within which we're searching
                True,  # since we're using Geography objects, this flag enables spheroid-based calculatitudeions
            )
        )
        .options(  # this method chain allows us to specify eager loading behavior
            selectinload(  # since we're using async/session interface, loading needs to happen in query context
                Site.equipment
            ),
            selectinload(Site.amenities),
            selectinload(Site.sports_facilities),
            selectinload(Site.reviews),
            selectinload(Site.reports),
        )
    )

    logging.debug("Query SQL: %s", str(query_sql))

    #  add filters based on optional query parameters

    # logging.info("Query flag: RELEASE TYPE: %s", str(release_type))
    logging.debug("Query SQL: %s", str(query_sql))

    logging.info("\n\n**** TRANSACTION ****\n")

    try:
        # send query to db by calling async session
        async with Session as s:
            logging.info("Transaction: BEGIN")
            async with s.begin():
                logging.info("SESSION: Checked out a connection")
                res = await s.execute(query_sql.with_session(s).statement)
                # context manager autocommits the query
                logging.info("QUERY: Submitted")
                res = res.scalars().all()  # decode results

                sites = []

                # now that we have our sites, we need to remove sites that don't meet the user's filter criteria
                # the pattern commented in the loop below is followed for the following 2 loops- ommitting comments there
                for site in res:
                    pass_flag = (
                        False  # this flag is triggered if a filter condition is not met
                    )

                    if equipment:  # if they have an equipment filter provided
                        eq_dict = site.equipment[0].__dict__
                        for eq in equipment:  # check the equipment in the filter
                            if eq_dict[eq] == 0:  # if they don't have it
                                pass_flag = True  # don't add this site to the response

                    if amenities:  # as above for amenities filter
                        amenities_dict = site.amenities[0].__dict__
                        for amenity in amenities:
                            if not amenities_dict[amenity]:
                                pass_flag = True

                    if sports_facilities:  # as above for sports facilities filter
                        facilities_dict = site.sports_facilities[0].__dict__
                        for facility in sports_facilities:
                            if not facilities_dict[facility]:
                                pass_flag = True

                    if (
                        not pass_flag
                    ):  # as long as the flag isn't triggered, add the site to the response
                        # alas the days when I could do this in a list comprehension...
                        # anyway, let's instantiate some schemas

                        site_schema = await make_site_schema_response(site)

                        sites.append(
                            site_schema
                        )  # all matching sites are added to the response object

                logging.info("TRANSACTION: CLOSED")

        logging.info("SESSION: returned connection to the pool")
        logging.info("\n*** END TRANSACTION ***\n")
        # db session is closed by this point

        logging.info("\n*** RESULT ***\n")

        if len(sites) == 0:
            logging.info("QUERY: NO RESULTS -- Endpoint Service COMPLETE\n\n")

        logging.info("QUERY: Results returned -- endpoint service COMPLETE\n\n")
        return sites

    except Exception as e:
        logging.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve query results from database",
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
