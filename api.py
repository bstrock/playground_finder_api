from fastapi import FastAPI, Query as FQ
from sqlalchemy.orm import sessionmaker, Query
from typing import Optional, List
from table_models import Site
from schemas import SiteSchema
from create_spatial_db import SpatialDB
from geoalchemy2 import WKTElement
import uvicorn
from icecream import ic

app = FastAPI()

engine = SpatialDB.init()
Session = sessionmaker(engine)


@app.get("/query")
async def query(
        lat: float,
        lon: float,
        release_type: Optional[str] = None,
        carcinogen: Optional[bool] = None,
        sectors: Optional[list] = FQ([]),
        radius: int = 5,
):

    query_point = WKTElement(f"POINT({lon} {lat})", srid=4269)

    query_sql = Query([Site]).filter(
        Site.geom.ST_DWithin(
            query_point, radius
        )
    )

    if carcinogen:
        query_sql = query_sql.filter(Site.carcinogen == True)

    with Session() as s:
        with s.begin():
            print('send')
            res = query_sql.with_session(s).all()

        candidates = [SiteSchema.from_orm(site) for site in res]
    ic()
    ic(sectors)

    if not release_type:
        if not sectors:
            return candidates

    ic()
    if release_type:
        for site in candidates:
            types = site.release_types
            if release_type not in types:
                candidates.remove(site)
    ic()
    if sectors:
        counter = 0
        ic(sectors)
        for this_sector in sectors:
            for site in candidates:
                site_sector = site.sector
                if this_sector == site_sector:
                    counter += 1
                    ic(this_sector, site_sector)
                    candidates.remove(site)

    ic(len(candidates))
    ic(counter)
    return candidates


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)