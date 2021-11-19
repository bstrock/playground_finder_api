from geoalchemy2 import Geometry
from sqlalchemy import (
    String,
    BigInteger,
    Column,
    ForeignKey,
    Integer,
    DateTime,
    ARRAY,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

from models.enums import enums

# TABLES DEFINED HERE

# configure table base
Base = declarative_base()


class Site(Base):
    __tablename__ = "sites"
    __mapper_args__ = {"eager_defaults": True}

    site_id = Column(String, primary_key=True)
    site_name = Column(String(100), nullable=False)
    substrate_type = Column(enums.make(kind="substrate_types"))
    addr_street1 = Column(String(100), nullable=False)
    addr_street2 = Column(String(100), nullable=True)
    addr_city = Column(String(100), nullable=False)
    addr_state = Column(String(2), nullable=False)
    addr_zip = Column(Integer, nullable=False)
    geom = Column(Geometry(geometry_type="POLYGON", srid=4326))


class Equipment(Base):
    __tablename__ = "equipment"
    __mapper_args__ = {"eager_defaults": True}

    site_id = Column(
        String, ForeignKey("sites.site_id", name="equipment_key"), primary_key=True
    )

    diggers = Column(Integer, nullable=True)
    ladders = Column(Integer, nullable=True)
    toddler_swings = Column(Integer, nullable=True)
    standard_swings = Column(Integer, nullable=True)
    tire_swings = Column(Integer, nullable=True)
    accessible_swings = Column(Integer, nullable=True)
    seesaws = Column(Integer, nullable=True)
    climbers = Column(Integer, nullable=True)
    spinners = Column(Integer, nullable=True)
    bridges = Column(Integer, nullable=True)
    tunnels = Column(Integer, nullable=True)
    slides = Column(Integer, nullable=True)
    thematic = Column(Integer, nullable=True)
    ropes = Column(Integer, nullable=True)
    fire_poles = Column(Integer, nullable=True)
    staircases = Column(Integer, nullable=True)
    musical = Column(Integer, nullable=True)
    play_towers = Column(Integer, nullable=True)
    telephones = Column(Integer, nullable=True)
    binoculars = Column(Integer, nullable=True)
    tactile = Column(Integer, nullable=True)

    site = relationship("Site", backref="equipment", lazy=False)


class Amenities(Base):
    __tablename__ = "amenities"
    __mapper_args__ = {"eager_defaults": True}

    site_id = Column(
        String, ForeignKey("sites.site_id", name="amenities_key"), primary_key=True
    )

    splash_pad = Column(Integer, nullable=True)
    beach = Column(Integer, nullable=True)
    changing_rooms = Column(Integer, nullable=True)
    waterfront = Column(Integer, nullable=True)
    concessions = Column(Integer, nullable=True)
    rentals = Column(Integer, nullable=True)
    indoor_restroom = Column(Integer, nullable=True)
    portable_restroom = Column(Integer, nullable=True)
    trails = Column(Integer, nullable=True)
    picnic_tables = Column(Integer, nullable=True)
    benches = Column(Integer, nullable=True)
    shelter = Column(Integer, nullable=True)
    sun_shades = Column(Integer, nullable=True)
    grills = Column(Integer, nullable=True)

    site = relationship("Site", backref="amenities", lazy=False)


class SportsFacilities(Base):
    __tablename__ = "sports_facilities"
    __mapper_args__ = {"eager_defaults": True}

    site_id = Column(
        String,
        ForeignKey("sites.site_id", name="sports_facilities_key"),
        primary_key=True,
    )

    skate_park = Column(Integer, nullable=True)
    tennis_court = Column(Integer, nullable=True)
    hockey_rink = Column(Integer, nullable=True)
    soccer_field = Column(Integer, nullable=True)
    basketball_court = Column(Integer, nullable=True)
    baseball_diamond = Column(Integer, nullable=True)

    site = relationship("Site", backref="sports_facilities", lazy=False)


class User(Base):
    __tablename__ = "users"
    __mapper_args__ = {"eager_defaults": True}

    email = Column(String(50), unique=True, primary_key=True)
    hashed_password = Column(String(100), nullable=False)  # these will be hashed
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    favorite_parks = Column(ARRAY(String, dimensions=1), server_default="{}")


class Review(Base):
    __tablename__ = "reviews"
    __mapper_args__ = {"eager_defaults": True}

    review_id = Column(BigInteger, autoincrement=True, primary_key=True)
    user_email = Column(
        String, ForeignKey("users.email", name="reviews_key"), nullable=False
    )
    site_id = Column(String, ForeignKey("sites.site_id", name="site_reviews_key"))
    comment = Column(Text, nullable=True)
    stars = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    site = relationship("Site", backref="reviews", lazy=False)
    user = relationship("User", backref="reviews", lazy=False)


# report table
class Report(Base):
    __tablename__ = "reports"
    __mapper_args__ = {"eager_defaults": True}

    report_id = Column(BigInteger, autoincrement=True, primary_key=True)
    site_id = Column(
        String, ForeignKey("sites.site_id", name="reports_site_key"), nullable=False
    )
    user_email = Column(
        String, ForeignKey("users.email", name="reports_user_key"), nullable=False
    )
    report_type = Column(
        enums.make(kind="report_types"), nullable=False
    )  # enumeration creation from values in enum.py
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    comment = Column(Text, nullable=True)
    equipment = Column(String(20), nullable=True)

    site = relationship("Site", backref="reports", lazy=False)
    user = relationship("User", backref="reports", lazy=False)
