from fastapi import FastAPI, Query as fastapi_Query
from sqlalchemy.orm import sessionmaker, Query
from sqlalchemy.ext.asyncio import AsyncSession
from create_spatial_db import SpatialDB
from geoalchemy2 import WKTElement
from typing import Optional, List
from schemas import SiteSchema
from table_models import Site
from icecream import ic
import logging
import uvicorn

app = FastAPI()

engine = SpatialDB.init()
Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

logging.basicConfig(
                    format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level="INFO",
                    )


@app.get("/query")
async def query(
        lat: float,
        lon: float,
        radius: int,
        release_type: Optional[str] = None,
        carcinogen: Optional[bool] = None,
        sectors: Optional[List[str]] = fastapi_Query(None),
) -> List[SiteSchema]:

    logging.info("Query received")

    query_point = WKTElement(f"POINT({lon} {lat})", srid=4269)

    logging.info("Query point: %s", query_point.desc)

    query_sql = Query([Site]).filter(
        Site.geom.ST_DWithin(
            query_point, radius
        )
    )

    logging.debug("Query SQL: %s", str(query_sql))

    if carcinogen:
        query_sql = query_sql.filter(Site.carcinogen == True)

        logging.info("Query flag: CARCINOGEN")
        logging.debug("Query SQL: %s", str(query_sql))

    if sectors:
        query_sql = query_sql.filter(Site.sector.in_(sectors))

        logging.info("Query flag: SECTORS: %s", str(sectors))
        logging.debug("Query SQL: %s", str(query_sql))

    async with Session() as s:
        logging.info("Transaction: BEGIN")
        async with s.begin():
            logging.info("Session has checked out a connection")
            res = await s.execute(query_sql.with_session(s).statement)

            logging.info("Query: SUBMITTED")
        logging.info("Transaction: END\n")
        res = res.scalars()
        candidates = [SiteSchema.from_orm(site) for site in res]

        logging.info("Query: Results unpacked")
    logging.info("Session has returned connection to the pool")

    if len(candidates) == 0:
        logging.info("Query: NO RESULTS -- Endpoint Service Complete\n\n")
        return candidates

    if not release_type:
        logging.info("Query: Returning results -- Endpoint Service Complete\n\n")
        return candidates

    elif release_type:
        logging.info("Query flag: RELEASE TYPE: %s", release_type)
        resp = []
        for site in candidates:
            types = site.release_types
            keep_flag = 0
            for i, t in enumerate(types):
                if t == release_type:
                    keep_flag += 1
            if keep_flag > 0:
                resp.append(site)

        if len(resp) == 0:
            logging.info("Query: NO RESULTS -- Endpoint Service Complete\n\n")
        else:
            logging.info("Query: Returning results -- Endpoint Service Complete\n\n")
        return resp


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)