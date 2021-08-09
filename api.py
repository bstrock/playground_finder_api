from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from fastapi import FastAPI, Query as fastapi_Query, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker, Query, selectinload, with_polymorphic
from create_spatial_db import SpatialDB
from geoalchemy2 import WKTElement
from typing import Optional, List
from schemas import SiteSchema, ReportSchema, Globals, ChildReportSchema
from table_models import Site, Report, ActivityReports, EmissionReports, UnusedReports
import logging
import uvicorn
from icecream import ic

# initializations
app = FastAPI()
engine = create_async_engine(url=SpatialDB.url, echo=True, future=True)
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
            logging.info("TRANSACTION: CLOSED\n")


        logging.info("SESSION: returned connection to the pool")

        # db session is closed here


        logging.info("QUERY: Results unpacked")

        if len(sites) == 0:
            logging.info("QUERY: NO RESULTS -- Endpoint Service COMPLETE\n\n")

        logging.info("QUERY: Results returned -- endpoint service COMPLETE\n\n")
        return sites


@app.post("/submit")
async def submit(
        report: ReportSchema,
        Session: AsyncSession = Depends(get_db),
):

    """main_report = Report(
        site_id=report.site_id,
        report_type=report.report_type
    )

    if report.message:
        main_report.message = report.message

    if report.emission_type:
        main_report

    elif report.activity_type:
        main_report.activity_type = report.activity_type

    elif report.unused_type:
        main_report.unused_type=report.unused_type"""
    data = jsonable_encoder(report)
    ic(data)

    exclude = ['message', 'site_id', 'report_type']

    for i, sub in enumerate(Globals.SUB_REPORTS):
        for k in data.keys():
            if k in sub.__dict__.keys() and k not in exclude and data[k] is not None:
                ic(k, sub)
                child = sub()
                break

    for k in data:
        if data[k] is not None:
            child.__setattr__(k, data[k])

    async with Session as s:
        async with s.begin():
            s.add(child)

    return child


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)