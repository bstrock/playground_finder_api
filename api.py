from fastapi import FastAPI, Query as fastapi_Query, Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from create_spatial_db import SpatialDB
from sqlalchemy.orm import sessionmaker, Query
from geoalchemy2 import WKTElement
from typing import Optional, List
from schemas import SiteSchema
from table_models import Site
import logging
import uvicorn

# initializations
app = FastAPI()
engine = create_async_engine(url=SpatialDB.url, echo=False, future=True)
Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# dependency for injection
async def get_db():
    s = Session()
    try:
        yield s
    finally:
        await s.close()


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
        Session: AsyncSession = Depends(get_db)

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

    if release_type:
        query_sql = query_sql.filter(Site.release_types.any(release_type))

    async with Session as s:
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)