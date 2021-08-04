from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.engine import URL
from table_models import Base
import os

class SpatialDB:

    # connection parameters
    username = os.environ.get("USERNAME")
    password = os.environ.get("PASSWORD")

    url = URL.create(
        drivername="postgresql+psycopg2",
        username=username,
        password=password,
        host="localhost",
        port=5432,
        database="tri_app"
    )

    # configure engine
    @staticmethod
    def init():
        # use to create engine for SQLAlchemy connection or Session
        return create_engine(url=SpatialDB.url, echo=False, future=True)

    @staticmethod
    def make_db(engine):
        # use to create all tables defined in models.py
        # models must inherit from Base
        Base.metadata.create_all(engine, checkfirst=True)

    @staticmethod
    def reset_db(engine):
        # use to drop all tables when resetting database
        Base.metadata.drop_all(engine)  # uncomment and run to wipe tables and rebuild (NOTE: lossy, obv)

    @staticmethod
    def enable_PostGIS(engine):
        # if initializing spatial db, use to enable PostGIS extension
        enable = text("CREATE EXTENSION postgis")  # text construct is necessary here

        with engine.connect() as conn:
            with conn.begin():
                conn.execute(enable)

    @staticmethod
    def count_tables(engine):
        meta = MetaData()
        meta.reflect(bind=engine)

        count = len(meta.tables)
        print(f"This database contains {count} tables!")


# STUFF HAPPENS HERE
# generate and execute sql to make all the tables and things
if __name__ == "__main__":
    engine = SpatialDB.init()
    SpatialDB.reset_db(engine)
    #SpatialDB.enable_PostGIS(engine)
    SpatialDB.make_db(engine)
    SpatialDB.count_tables(engine)
