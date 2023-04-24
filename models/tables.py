from geoalchemy2 import Geometry
from sqlalchemy import (
    String,
    BigInteger,
    Column,
    ForeignKey,
    Integer,
    DateTime,
    Boolean
)
from sqlalchemy.orm import declarative_base, relationship

# TABLES DEFINED HERE

# configure table base
Base = declarative_base()


class Site(Base):
    __tablename__ = "sites"
    __mapper_args__ = {"eager_defaults": True}

    site_id = Column(String, primary_key=True)
    substrate_type = Column(String, nullable=True)
    site_name = Column(String(100), nullable=False)
    addr_street1 = Column(String(100), nullable=False)
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

    bouncers = Column(Integer, nullable=True)
    bridges = Column(Integer, nullable=True)
    climbers = Column(Integer, nullable=True)
    diggers = Column(Integer, nullable=True)
    fire_poles = Column(Integer, nullable=True)
    monkey_bars = Column(Integer, nullable=True)
    toddler_swings = Column(Integer, nullable=True)
    standard_swings = Column(Integer, nullable=True)
    accessible_swings = Column(Integer, nullable=True)
    seesaws = Column(Integer, nullable=True)
    spinners = Column(Integer, nullable=True)
    tunnels = Column(Integer, nullable=True)
    slides = Column(Integer, nullable=True)
    staircases = Column(Integer, nullable=True)
    play_towers = Column(Integer, nullable=True)

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
    disc_golf = Column(Integer, nullable=True)
    foursquare = Column(Integer, nullable=True)
    badminton = Column(Integer, nullable=True)
    tennis_court = Column(Integer, nullable=True)
    hockey_rink = Column(Integer, nullable=True)
    soccer_field = Column(Integer, nullable=True)
    basketball_court = Column(Integer, nullable=True)
    baseball_diamond = Column(Integer, nullable=True)
    volleyball = Column(Integer, nullable=True)
    horseshoes = Column(Integer, nullable=True)

    site = relationship("Site", backref="sports_facilities", lazy=False)


class Episodes(Base):
    __tablename__ = 'episodes'
    __mapper_args__ = {"eager_defaults": True}

    id = Column(BigInteger, primary_key=True)
    title = Column(String, nullable=True)
    audio_url = Column(String, nullable=True)
    artwork_url = Column(String, nullable=True)
    description = Column(String, nullable=True)
    summary = Column(String, nullable=True)
    artist = Column(String, nullable=True)
    tags = Column(String, nullable=True)
    published_at = Column(DateTime)
    duration = Column(Integer, nullable=True)
    hq = Column(Boolean)
    guid = Column(String, nullable=True)
    inactive_at = Column(DateTime, nullable=True)
    episode_number = Column(Integer)
    season_number = Column(Integer)
    explicit = Column(Boolean)
    private = Column(Boolean)
    total_plays = Column(Integer)
    magic_mastering = Column(Boolean)
    custom_url = Column(String, nullable=True)

