from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, MetaData
from sqlalchemy.engine import URL
from models.tables import Base
import asyncio
import os


class SpatialDB:

    # connection parameters
    username = os.environ.get("USERNAME")
    password = os.environ.get("PASSWORD")
    url = os.environ.get("SECRET_URL")

    engine = create_async_engine(url=url, echo=False, future=True)

    # configure engine
    @staticmethod
    def init():
        # use to create engine for SQLAlchemy connection or Session
        return sessionmaker(
            SpatialDB.engine, class_=AsyncSession, expire_on_commit=False
        )

    @staticmethod
    async def make_db():
        # use to create all tables defined in models.py
        # models must inherit from Base
        async with SpatialDB.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @staticmethod
    async def reset_db():
        # use to drop all tables when resetting database
        async with SpatialDB.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    @staticmethod
    async def enable_PostGIS(engine):
        # if initializing spatial db, use to enable PostGIS extension
        enable = text("CREATE EXTENSION postgis")  # text construct is necessary here

        async with engine.begin() as conn:
            await conn.execute(enable)

    @staticmethod
    def count_tables(engine):
        meta = MetaData()
        meta.reflect(bind=engine)

        count = len(meta.tables)
        print(f"This database contains {count} tables!")


async def main():
    engine = SpatialDB.init()
    await SpatialDB.enable_PostGIS(engine)
    await SpatialDB.reset_db()

    await SpatialDB.make_db()
    # SpatialDB.count_tables(engine)


# STUFF HAPPENS HERE
# generate and execute sql to make all the tables and things
if __name__ == "__main__":
    asyncio.run(main())
