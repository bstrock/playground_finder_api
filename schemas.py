from pydantic import BaseModel
from typing import Dict, Optional


class Chemical(BaseModel):
    unit: str
    total: float

    class Config:
        orm_mode = True


class SiteSchema(BaseModel):
    site_id: str
    name: str
    address: str
    city: str
    state: str
    zip: int
    latitude: float
    longitude: float
    sector: str
    carcinogen: bool
    chemicals: Dict[str, Chemical]
    release_types: list
    total_releases: float

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class ReportSchema(BaseModel):
    site_id: str
    report_type: str
    message: str
    emission_type: Optional[str]
    activity_type: Optional[str]
    unused_type: Optional[str]

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True

