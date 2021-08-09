from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from fastapi import FastAPI, Query as fastapi_Query, Depends
from sqlalchemy.orm import sessionmaker, Query, selectinload, with_polymorphic
from create_spatial_db import SpatialDB
from geoalchemy2 import WKTElement
from typing import Optional, List
from schemas import SiteSchema, ReportSchema, Globals
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
                for result in res:
                    ic(result.reports)
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
) -> ReportSchema:

    main_report = Report(
        site_id=report.site_id,
        report_type=report.report_type
    )

    if report.message:
        main_report.message = report.message

    if report.emission_type:
        linked_report = EmissionReports(
            emission_type=report.emission_type
        )

    elif report.activity_type:
        linked_report = ActivityReports(
            activity_type=report.activity_type
        )

    elif report.unused_type:
        linked_report = UnusedReports(
            unused_type=report.unused_type
        )

    async with Session as s:
        async with s.begin():
            s.add(main_report)
            await s.commit()
            ic(main_report.__dict__)
        async with s.begin():
            s.add(linked_report)

    return report

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)