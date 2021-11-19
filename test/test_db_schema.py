import os

import pytest
from sqlalchemy.engine import create_engine, URL
from sqlalchemy.orm import sessionmaker

from models.tables import Site, Equipment, Amenities, SportsFacilities, User

username = os.environ.get("USERNAME")
password = os.environ.get("PASSWORD")

# points to localhost
url = URL.create(
    drivername="postgresql+psycopg2",
    username=username,
    password=password,
    host="localhost",
    port=5432,
    database="brianstrock",
)

engine = create_engine(url)
Session = sessionmaker(engine)
DATA_LENGTH = 29


def query_table(table):
    # how we get our test query results
    with Session() as s:
        with s.begin():
            return s.query(table).all()


def test_fake_users(startup):
    # does not use query_table as it needs to be done in the session

    with Session() as s:
        with s.begin():
            res = s.query(User).all()

        assert len(res) == 3  # correct # of fake users, after running test_api.py

        for user in res:
            assert user.email  # make sure they have a valid email


def test_sites_content():
    # gets its own test due to expected None value

    res = query_table(Site)  # get table

    assert len(res) == DATA_LENGTH  # check length

    # except for the expected None, make sure there's a value in the cell
    for site in res:
        keys = list(vars(site))
        for key in keys:
            if "street_addr2" not in key:
                assert key


@pytest.fixture
def test_table_list():
    # this gets the rest of the classes, which can be tested together in one function

    return [Amenities, Equipment, SportsFacilities]


def test_table_content(test_table_list):

    for table in test_table_list:
        res = query_table(table)  # get the table results

        assert len(res) == DATA_LENGTH  # check the lenth

        for row in res:  # iterate through rows
            keys = list(vars(row))  # grab keys
            for key in keys:
                val = row.__dict__[key]  # assign row value based on key
                # ensure the value is either a valid something, or if it comes back as zero, it's actually zer0
                # not just falsy

                assert type(val) == int if val == 0 else val
