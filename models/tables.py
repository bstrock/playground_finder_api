from sqlalchemy import (
    String,
    BigInteger,
    Column,
    Integer,
    ForeignKey,
    Float,
    Boolean,
    JSON,
    DateTime,
    ARRAY,
)
from sqlalchemy.orm import declarative_base, relationship
from geoalchemy2 import Geography
from sqlalchemy.sql import func
from models.enums import enums

# TABLES DEFINED HERE

# configure table base
Base = declarative_base()


class Site(Base):
    __tablename__ = "sites"
    __mapper_args__ = {"eager_defaults": True}

    site_id = Column(String, primary_key=True)
    name = Column(String(100), nullable=False)
    address = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    county = Column(String(100), nullable=False)
    state = Column(String(2), nullable=False)
    zip = Column(Integer, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    sector = Column(enums.make(kind="industry_sectors"), nullable=False)
    carcinogen = Column(Boolean, nullable=False)
    chemicals = Column(JSON, nullable=False)
    release_types = Column(ARRAY(String), nullable=False)
    total_releases = Column(Float, nullable=False)
    geom = Column(Geography(geometry_type="POINT", srid=4326))

    def __init__(
        self,
        site_id,
        name,
        address,
        city,
        county,
        state,
        zip,
        latitude,
        longitude,
        sector,
        carcinogen,
        chemicals,
        release_types,
        total_releases,
        geom,
    ):
        self.site_id = site_id
        self.name = name
        self.address = address
        self.city = city
        self.county = county
        self.state = state
        self.zip = int(zip)
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.sector = sector
        self.carcinogen = carcinogen
        self.chemicals = chemicals
        self.release_types = release_types
        self.total_releases = float(total_releases)
        self.geom = geom


# report table
class Report(Base):
    __tablename__ = "reports"

    report_id = Column(BigInteger, autoincrement=True, primary_key=True)
    site_id = Column(
        String, ForeignKey("sites.site_id", name="sites_key"), nullable=False
    )
    message = Column(String(240), nullable=True)
    report_type = Column(
        enums.make(kind="report_types"), nullable=False
    )  # enumeration creation from values in enum.py
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    site = relationship("Site", backref="reports", lazy=False)

    __mapper_args__ = {
        "eager_defaults": True,
        "polymorphic_identity": "report",
        "polymorphic_on": report_type,
        "with_polymorphic": "*",
    }


# linked tables
class EmissionReports(Report):
    __tablename__ = "emission_reports"
    __mapper_args__ = {"eager_defaults": True, "polymorphic_identity": "Emission"}

    report_id = Column(
        BigInteger,
        ForeignKey("reports.report_id", name="emissions_key"),
        primary_key=True,
    )
    emission_type = Column(enums.make("emission_types"), nullable=False)
    report = relationship("Report", backref="Emission", lazy=False)


class ActivityReports(Report):
    __tablename__ = "activity_reports"
    __mapper_args__ = {"eager_defaults": True, "polymorphic_identity": "Active Site"}

    report_id = Column(
        BigInteger,
        ForeignKey("reports.report_id", name="active_sites_key"),
        primary_key=True,
    )
    activity_type = Column(enums.make("activity_types"), nullable=False)
    report = relationship("Report", backref="Active Site", lazy=False)


class UnusedReports(Report):
    __tablename__ = "unused_reports"
    __mapper_args__ = {"eager_defaults": True, "polymorphic_identity": "Inactive Site"}

    report_id = Column(
        BigInteger,
        ForeignKey("reports.report_id", name="inactive_sites_key"),
        primary_key=True,
    )
    unused_type = Column(enums.make("unused_types"), nullable=False)
    report = relationship("Report", backref="Inactive Site", lazy=False)
