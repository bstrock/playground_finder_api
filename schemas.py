from pydantic import BaseModel
from geoalchemy2 import WKTElement
from typing import List, Dict

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
    chemicals: dict
    release_types: list
    total_releases: float

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True
