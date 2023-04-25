import logging
from datetime import datetime
from typing import Optional, List, Dict

import pytz
import uvicorn
from fastapi import FastAPI, Query as fastapi_Query, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from geoalchemy2 import func
from geojson import FeatureCollection
from icecream import ic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Query, selectinload

from dependencies import (
    get_db,
    make_site_geojson,
    miles_to_meters,
)
from playground_planner.models.tables import Site, Episodes

app = FastAPI()

# ENABLE CORS
origins = ["*"]

# this is definitely important so that something works
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    radius: float = Depends(miles_to_meters),
    equipment: Optional[str] = fastapi_Query(None),
    amenities: Optional[str] = fastapi_Query(None),
    sports_facilities: Optional[str] = fastapi_Query(None),
    Session: AsyncSession = Depends(get_db),
) -> FeatureCollection:
    logging.info("Query received")
    logging.info("\n\n***QUERY PARAMETERS***\n")

    # prepare PostGIS geometry object
    query_point = f"POINT({longitude} {latitude})"
    logging.info("Query point: %s", query_point)

    if equipment:
        equipment = equipment.split(",")
        if len(equipment) == 1:
            equipment = list(equipment)

    if amenities:
        amenities = amenities.split(",")
        if len(amenities) == 1:
            amenities = list(amenities)

    if sports_facilities:
        sports_facilities = sports_facilities.split(",")
        if len(sports_facilities) == 1:
            sports_facilities = list(sports_facilities)

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

                        site_geojson = await make_site_geojson(site)

                        sites.append(
                            site_geojson
                        )  # all matching sites are added to the response object

                logging.info("TRANSACTION: CLOSED")

        logging.info("SESSION: returned connection to the pool")
        logging.info("\n*** END TRANSACTION ***\n")
        # db session is closed by this point

        logging.info("\n*** RESULT ***\n")

        if len(sites) == 0:
            logging.info("QUERY: NO RESULTS -- Endpoint Service COMPLETE\n\n")

        logging.info("QUERY: Results returned -- endpoint service COMPLETE\n\n")
        response_geojson = FeatureCollection(sites)
        ic(len(response_geojson["features"]))
        return response_geojson

    except Exception as e:
        logging.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve query results from database",
        )


async def retrieve_episodes(session: AsyncSession) -> List[Dict]:
    results = []
    async with session.begin():
        res = await session.execute(select(Episodes))
        for r in res.scalars().all():
            appended = r.__dict__
            appended.pop("_sa_instance_state")
            results.append(appended)
    return results


@app.get("/episodes")
async def get_episodes(Session: AsyncSession = Depends(get_db)) -> ...:
    async with Session as s:
        results = retrieve_episodes(session=s)
    return results


@app.post("/update")
async def update_episodes(Session: AsyncSession = Depends(get_db)) -> ...:
    import os
    import requests

    headers = {"Content-Type": "application/json", "charset": "utf-8"}
    podcast_id = 2009882
    res = requests.get(
        url=f'https://buzzsprout.com/api/{podcast_id}/episodes.json?api_token={os.environ.get("API_KEY")}',
        headers=headers,
    )

    if res.ok:
        episodes_data = res.json()
        [
            ep.update(
                {
                    "published_at": datetime.fromisoformat(ep.get("published_at"))
                    .astimezone(pytz.UTC)
                    .replace(tzinfo=None)
                }
            )
            for ep in episodes_data
        ]

        async with Session as s:
            async with s.begin():
                episodes_in_db = retrieve_episodes(s)
                existing_episode_ids = [ep.get("id") for ep in episodes_in_db]
                eps_updates = [
                    Episodes(**ep)
                    for ep in episodes_data
                    if ep not in existing_episode_ids
                ]
                if eps_updates:
                    s.add_all(eps_updates)
                    await s.commit()

        return status.HTTP_200_OK
    else:
        # should raise error
        return status.HTTP_500_INTERNAL_SERVER_ERROR(
            "An error occurred while retrieving from buzzsprout!"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
