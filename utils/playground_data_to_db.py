import os
from typing import Callable, AnyStr

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from icecream import ic
from pandas import DataFrame
from passlib.context import CryptContext
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker

from playground_planner.models.tables import Site, Equipment, Amenities, SportsFacilities, Base, Episodes

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)


class PlaygroundLoader:
    # connection parameters
    username = os.environ.get("USERNAME")
    password = os.environ.get("PASSWORD")
    url = os.environ.get("SECRET_URL")

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    engine = create_engine(url=url, echo=False)
    Session = sessionmaker(engine)

    def __init__(self):
        self.data = None
        self.sites = None
        self.inserts = {
            "sites": [],
            "equipment": [],
            "amenities": [],
            "sports_facilities": [],
            "users": [],
            'episodes': []
        }

    def set_data(self, data: DataFrame):
        # sets data object used in program

        data = data.reset_index()
        data = data.set_index("USER_SITE_")  # sorry for the janky columns
        self.data = data

    def class_from_row(
            self,
            row: pd.Series,
            class_to_use: Callable,
            key: AnyStr,
            index_col: AnyStr
    ):
        #### EXTREMELY USEFUL
        # create class object for model: Site, Equipment, Amenity, etc. using abstract factory pattern
        table_row = class_to_use()

        for col in row.index:  # grab the row columns
            # give our model object these attributes
            val = row[col]
            if isinstance(val, np.int64):
                val = int(val)
            setattr(table_row, col.lower(), val)

        setattr(table_row, index_col, row._name)  # set site id attribute

        # no you can't use a ternary operator for this
        self.inserts[key].append(table_row)


    def import_data(self, path: str):
        # copies CSV schema from path and uses it to fill with random numbers 1-10
        # uses this function to make a row in a dataframe into the corresponding model object

        if path:
            table_schema = pd.read_csv(path, index_col="SITE_ID")  # its columns
            # here we check which class and method to use
            path_split = path.split("/")
            sentinel = path_split[-1]
        elif not path:
            sentinel = None
        if not sentinel:
            class_to_use  = Episodes
            table_schema = self.import_podcast_episodes()
            key = 'episodes'
        elif sentinel and sentinel == "equipment.csv":
            class_to_use = Equipment
            key = "equipment"
        elif sentinel and sentinel == "amenities.csv":
            class_to_use = Amenities
            key = "amenities"
        elif sentinel and sentinel == "sports_facilities.csv":
            class_to_use = SportsFacilities
            key = "sports_facilities"

        table_schema.columns = [col.lower() for col in table_schema.columns]
        ic(table_schema)
        # remember our really useful function?  now we just apply it to the dataframe...zwoop, row objects!
        table_schema.apply(
            lambda row: self.class_from_row(
                row=row, class_to_use=class_to_use, key=key, index_col="site_id" if sentinel else 'id'
            ),
            axis=1,
        )

    # %% site processing
    def data_to_sites(self):

        sites = self.data.index.unique().tolist()  # keys
        self.data.set_crs(epsg=4326, inplace=True)
        # loop through the playgrounds and make objects out of them
        for pg in sites:
            df = self.data.loc[pg]
            self.inserts["sites"].append(
                Site(
                    site_id=df.name,
                    site_name=df.SITE_NAME,
                    addr_street1=df.ADDR_STR_1,
                    addr_city=df.ADDR_CITY,
                    addr_state=df.ADDR_STATE,
                    addr_zip=int(df.ADDR_ZIP),
                    geom=f'SRID=4326;{df.geometry.wkt}'
                )
            )

    def import_podcast_episodes(self) -> pd.DataFrame:
        headers = {'Content-Type': 'application/json', 'charset': 'utf-8'}
        podcast_id = 2009882
        res = requests.get(
            url=f'https://buzzsprout.com/api/{podcast_id}/episodes.json?api_token={os.environ.get("API_KEY")}',
            headers=headers)
        if res.ok:
            episodes_data = res.json()
            ic(episodes_data)
            eps_df = pd.DataFrame(episodes_data)
            return eps_df

    def main(self):
        # let's do this

        path_base = "~/playground_planner/playground_planner/data"
        csv_path = path_base + "/csv/real"

        json_path = path_base + "/json/playgrounds.json"
        equipment_path = csv_path + "/equipment.csv"
        amenities_path = csv_path + "/amenities.csv"
        sports_facilities_path = csv_path + "/sports_facilities.csv"

        data = gpd.read_file(json_path)
        ic(data)

        keep_these_columns = [
            "USER_SITE_",
            "SITE_NAME",
            "SUBSTRATE_",
            "ADDR_STR_1",
            "ADDR_CITY",
            "ADDR_STATE",
            "ADDR_ZIP",
            "geometry",
        ]

        self.set_data(data=data[keep_these_columns])  # set data
        self.data_to_sites()  # generate sites
        self.import_data(equipment_path)  # import random data
        self.import_data(amenities_path)  # and one more time
        self.import_data(sports_facilities_path)
        self.import_data(None)

        # these are the lists of row objects we are inserting
        keys = list(self.inserts.keys())

        # scrub the db real quick here
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

        # yay for context managers
        # let's put some objects in our database

        for key in keys:  # loop through tables
            with self.Session() as s:
                with s.begin():
                    s.add_all(self.inserts[key])  # autocommit the whole dang thing

        # that's it, just a loop that loads everything in like 2 seconds, nothing to see here


# stuff runs here
if __name__ == "__main__":
    # set up some stuff

    # create the class object
    playground_loader = PlaygroundLoader()
    playground_loader.main()

    # that's a wrap
