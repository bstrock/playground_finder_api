import geopandas as gpd
import pandas as pd
from pandas import DataFrame
from models.tables import Site, Equipment, Amenities, SportsFacilities, User
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from utils.create_spatial_db import SpatialDB
from passlib.context import CryptContext
from sqlalchemy.engine import URL
import os
from icecream import ic
import numpy as np
import json

from icecream import ic
import asyncio
from datetime import datetime as dt

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)


class PlaygroundLoader:
    # connection parameters
    username = os.environ.get("USERNAME")
    password = os.environ.get("PASSWORD")
    # url = os.environ.get("SECRET_URL")

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # points to localhost
    url = URL.create(
        drivername="postgresql+asyncpg",
        username=username,
        password=password,
        host="localhost",
        port=5432,
        database="brianstrock",
    )

    engine = create_async_engine(url=url, echo=False, future=True)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    def __init__(self):
        self.data = None
        self.sites = None
        self.inserts = {
            'sites': [],
            'equipment': [],
            'amenities': [],
            'sports_facilities': [],
            'users': [],
        }

    def set_data(self, data: DataFrame):
        # sets data object used in program

        data = data.reset_index()
        data = data.set_index("USER_SITE_")  # sorry for the janky columns
        self.data = data

    def class_from_row(self, row, class_to_use, key, index_col):
        #### EXTREMELY USEFUL
        table_row = (
            class_to_use()
        )  # create class object for model: Site, Equipment, Amenity, etc.

        for col in row.index:  # grab the row columns
            setattr(
                table_row, col.lower(), row[col]
            )  # give our model object these attributes
        setattr(table_row, index_col, row._name)  # set site id attribute
        ic(table_row)
        # no you can't use a ternary operator for this
        self.inserts[key].append(table_row)

    def randomized_import(self, path: str):
        # copies CSV schema from path and uses it to fill with random numbers 1-10
        # uses this function to make a row in a dataframe into the corresponding model object

        # here we need to grab the table schema in order to generate fake data
        table_schema = pd.read_csv(path, index_col="SITE_ID")  # its columns
        shape = table_schema.shape  # its dimensions
        ic(shape)
        size = (29, shape[1])
        # here we check which class and method to use
        path_split = path.split("/")
        sentinel = path_split[-1]

        if sentinel == "equipment.csv":
            class_to_use = Equipment
            key = 'equipment'
            random_data = np.random.randint(
                0, 10, size=size
            )  # creates an array of random ints 0-10
        elif sentinel == "amenities.csv":
            class_to_use = Amenities
            key = 'amenities'
        elif sentinel == "sports_facilities.csv":
            class_to_use = SportsFacilities
            key = 'sports_facilities'

        if sentinel != "equipment.csv":
            random_data = np.random.choice(a=[1, 0], size=size, p=[0.25, 0.75])
        df = pd.DataFrame(
            random_data, columns=table_schema.columns, index=self.data.index
        )  # the actual dataframe we're using

        # remember our really useful function?  now we just apply it to the dataframe...zwoop, row objects!
        df.apply(
            lambda x: self.class_from_row(
                row=x, class_to_use=class_to_use, key=key, index_col="site_id"
            ),
            axis=1,
        )

    # %% site processing

    def data_to_sites(self):
        # this could get refactored into the randomized function style
        # like why declare attributes explicitly, amirite

        sites = self.data.index.unique().tolist()  # keys

        sites_to_db = []
        # loop through the playgrounds and make objects out of them
        for pg in sites:
            df = self.data.loc[pg]
            self.inserts['sites'].append(
                Site(
                    site_id=df.name,
                    site_name=df.SITE_NAME,
                    substrate_type=df.SUBSTRATE_,
                    addr_street1=df.ADDR_STR_1,
                    addr_city=df.ADDR_CITY,
                    addr_state=df.ADDR_STATE,
                    addr_zip=df.ADDR_ZIP,
                    geom=df.geometry.to_wkt(),
                )
            )

    def import_test_users(self, path):
        index_col = 'email'
        user_data_df = pd.read_csv(path, index_col=index_col)

        user_list = []

        for user in user_data_df.index.unique():
            this_user = user_data_df.loc[user]
            ic(this_user.name)
            user_object = User(
                email=this_user.name,
                hashed_password=self.pwd_context.hash(this_user.hashed_password),
                first_name=this_user.first_name,
                last_name=this_user.last_name
            )
            user_list.append(user_object)
        self.inserts['users'] = user_list


    # %%
    async def main(self):
        # let's do this

        # these are the lists of row objects we are inserting
        keys = list(self.inserts.keys())

        # scrub the db real quick here
        await SpatialDB.reset_db()

        # yay for context managers
        # let's put some objects in our database

        for key in keys:  # loop through tables
            async with self.Session() as s:
                async with s.begin():
                    s.add_all(self.inserts[key])  # autocommit the whole dang thing

        # that's it, just a loop that loads everything in like 2 seconds, nothing to see here


# stuff runs here

if __name__ == "__main__":
    # set up some stuff
    path_base = "~/Documents/777/playground_planner/data"
    fake_csv_path = path_base + "/csv/fake"

    json_path = path_base + "/json/playgrounds.json"
    equipment_path = fake_csv_path + "/equipment.csv"
    amenities_path = fake_csv_path + "/amenities.csv"
    sports_facilities_path = fake_csv_path + "/sports_facilities.csv"
    fake_users_path = fake_csv_path + "/users.csv"

    data = gpd.read_file(json_path)

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

    # create the class object
    playground_loader = PlaygroundLoader()

    playground_loader.set_data(data=data[keep_these_columns])  # set data
    playground_loader.data_to_sites()  # generate sites
    playground_loader.randomized_import(equipment_path)  # import random data
    playground_loader.randomized_import(amenities_path)  # and one more time
    playground_loader.randomized_import(sports_facilities_path)
    playground_loader.import_test_users(fake_users_path)
    asyncio.run(playground_loader.main())  # get that business into the db

    # that's a wrap
