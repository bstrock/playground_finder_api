from icecream import ic
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from fastapi import FastAPI, Query as fastapi_Query, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import sessionmaker, Query, selectinload
from sqlalchemy import select
from create_spatial_db import SpatialDB
from geoalchemy2 import WKTElement
from typing import Optional, List
from schemas import SiteSchema, ReportSchema, Globals
from table_models import Site, Report
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
        access_token: str,
        release_type: Optional[str] = None,
        carcinogen: Optional[bool] = None,
        sectors: Optional[List[str]] = fastapi_Query(None),
        Session: AsyncSession = Depends(get_db),
) -> List[SiteSchema]:

    logging.info("Query received")
    logging.info("\n\n***QUERY PARAMETERS***\n")

    if access_token == Globals.SECRET_KEY:

        # prepare PostGIS geometry object
        query_point = WKTElement(f"POINT({lon} {lat})", srid=4269)

        logging.info("Query point: %s", query_point.desc)

        # build spatial query
        query_sql = Query([Site]).filter(
            Site.geom.ST_DWithin(
                query_point, radius
            )
        ).options(selectinload(Site.reports))

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

                sites = [SiteSchema.from_orm(site) for site in res]  # unpack results to pydantic schema using list comprehension
            logging.info("TRANSACTION: CLOSED")


        logging.info("SESSION: returned connection to the pool")
        logging.info("\n*** END TRANSACTION ***\n")
        # db session is closed here


        logging.info("\n*** RESULT ***\n")

        if len(sites) == 0:
            logging.info("QUERY: NO RESULTS -- Endpoint Service COMPLETE\n\n")

        logging.info("QUERY: Results returned -- endpoint service COMPLETE\n\n")
        return sites


@app.post("/submit", response_model=ReportSchema)
async def submit(
        report: ReportSchema,
        Session: AsyncSession = Depends(get_db),
):

    data = jsonable_encoder(report) # it's just nice to have a dictionary

    # need to figure out which table model to base the report off of
    exclude = ['message', 'site_id', 'report_type']  # common to all reports
    for report_type in Globals.SUB_REPORTS:
        for k in data.keys():
            # each report type has a single unique column
            # we check if that column is in the report type schema, but not one of the common columns
            if k in report_type.__dict__.keys() and k not in exclude and data[k] is not None:
                report = report_type()  # we've found our report type- let's make an object
                break

    # we unpack the request submission into the report object
    for k in data:
        if data[k] is not None:
            report.__setattr__(k, data[k])

    async with Session as s:
        async with s.begin():
            s.add(report)

    return report

@app.get("/reports")
async def get_all_reports(access_token: str,
                          Session = Depends(get_db)
                          ) -> List[ReportSchema]:

    if access_token == Globals.SECRET_KEY:
        async with Session as s:
            async with s.begin():
                stmt = select(Report)
                res = await s.execute(stmt)
    ic(res)
    reports = res.scalars().all()

    response = [ReportSchema.from_orm(report) for report in reports]

    return response

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)