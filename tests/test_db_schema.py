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

def test_db_schema():
    engine = SpatialDB.engine
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)