import pandas as pd
from pandas import DataFrame
from models.tables import Site
from utils.create_spatial_db import SpatialDB
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import array
from icecream import ic
import asyncio
from datetime import datetime as dt

# rename columns

# columns have awkward names like -> 64. POTW - TOTAL TRANSFERS
# we want them to be nice like -> potw_total_transfers


class TRILoader:
    GRAMS_TO_POUNDS = 0.00220462
    engine = SpatialDB.engine
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    def __init__(self):
        self.data = None
        self.sites = None

    def set_data(self, data: DataFrame):
        self.data = data

    def rename_columns(self):

        for col in self.data.columns:
            split = col.split(".")  # separates out leading integer
            new = split[-1]  # captures only the last part of the split as column name
            new = new[1:].lower().replace(" ", "_").strip("_-_")  # some cleanup
            self.data.rename(columns={col: new}, inplace=True)  # rename

    def filter_columns(self):
        columns = [
            "trifd",
            "facility_name",
            "street_address",
            "city",
            "county",
            "st",
            "zip",
            "latitude",
            "longitude",
            "industry_sector",
            "chemical",
            "carcinogen",
            "unit_of_measure",
            "total_releases",
            "fugitive_air",
            "stack_air",
            "water",
            "underground",
            "landfills",
            "surface_impndmnt",
            "land_treatment",
            "b_-_other_surface_i"
        ]

        self.data = self.data.filter(items=columns)

    # %% site processing

    def data_to_sites(self):

        sites = self.data["trifd"].unique().tolist()  # keys

        sites_to_db = []

        for site in sites:
            df = self.data[self.data.trifd == site]  # subset data for site
            check_carcinogen = df.carcinogen.unique()  # array of values
            carcinogen = (
                True if "YES" in check_carcinogen else False
            )  # site flagged True if any chemical is carcinogenic
            chemicals = {}  # placeholder
            geom = f"POINT({df.longitude.unique()[0]} {df.latitude.unique()[0]})"  # PostGIS string

            # determine site release handling
            types = []
            if df.fugitive_air.sum() > 0 or df.stack_air.sum() > 0:
                types.append("AIR")

            if df.water.sum() > 0:
                types.append("WATER")

            if (
                df.underground.sum() > 0
                or df.landfills.sum() > 0
                or df.surface_impndmnt.sum() > 0
                or df["b_-_other_surface_i"].sum() > 0
            ):
                types.append("LAND")

            total_releases = 0.0  # value counter

            # get row for each chemical at the site, record its unit and total, add total to releases
            for chemical in df.chemical.unique():
                row = df[df.chemical == chemical]
                unit = row["unit_of_measure"].iloc[0]
                total = row["total_releases"].iloc[0]

                total_releases += (
                    total if unit == "Pounds" else total * self.GRAMS_TO_POUNDS
                )

                chemicals[chemical] = {"unit": unit, "total": total}

            if len(types) == 0:
                types = [None]

            # instantiate row for this site
            this_site = Site(
                site_id=df.trifd.unique()[0],
                name=df.facility_name.unique()[0],
                address=df.street_address.unique()[0],
                city=df.city.unique()[0],
                county=df.county.unique()[0],
                state=df.st.unique()[0],
                zip=int(df.zip.unique()[0]),
                latitude=df.latitude.unique()[0],
                longitude=df.longitude.unique()[0],
                sector=df.industry_sector.unique()[0],
                carcinogen=carcinogen,
                chemicals=chemicals,
                release_types=array(types),
                total_releases=total_releases,
                geom=geom,
            )

            sites_to_db.append(this_site)

        self.sites = sites_to_db

    # %%
    async def main(self):
        # %% initialize db connections

        self.rename_columns()
        self.filter_columns()
        self.data_to_sites()

        await SpatialDB.reset_db()
        await SpatialDB.make_db()

        for site in self.sites:
            # create row in db)
            async with self.Session() as s:
                async with s.begin():
                    s.add(site)

        ic(dt.now())


# %%

if __name__ == "__main__":
    ic(dt.now())
    data = pd.read_csv("~/Downloads/tri_20_mn.csv")
    tri_loader = TRILoader()
    tri_loader.set_data(data=data)

    asyncio.run(tri_loader.main())
