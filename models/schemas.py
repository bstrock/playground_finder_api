from fastapi import HTTPException, status
from typing import Optional, List
from pydantic import BaseModel
import os


class ReportSchema(BaseModel):
    site_id: str
    report_type: str
    comment: Optional[str] = None
    equipment: Optional[str] = None

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class ReviewSchema(BaseModel):
    site_id: str
    stars: int
    email: Optional[str] = None
    comment: Optional[str] = None

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class EquipmentSchema(BaseModel):
    bouncers: int
    bridges: int
    climbers: int
    diggers: int
    fire_poles: int
    toddler_swings: int
    standard_swings: int
    accessible_swings: int
    seesaws: int
    spinners: int
    tunnels: int
    slides: int
    fire_poles: int
    staircases: int
    play_towers: int

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class AmenitiesSchema(BaseModel):
    splash_pad: Optional[bool]
    beach: Optional[bool]
    changing_rooms: Optional[bool]
    waterfront: Optional[bool]
    concessions: Optional[bool]
    rentals: Optional[bool]
    indoor_restroom: Optional[bool]
    portable_restroom: Optional[bool]
    trails: Optional[bool]
    picnic_tables: Optional[bool]
    benches: Optional[bool]
    shelter: Optional[bool]
    sun_shades: Optional[bool]
    grills: Optional[bool]

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class SportsFacilitiesSchema(BaseModel):
    skate_park: Optional[bool]
    tennis_court: Optional[bool]
    hockey_rink: Optional[bool]
    soccer_field: Optional[bool]
    basketball_court: Optional[bool]
    baseball_diamond: Optional[bool]

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class SiteSchema(BaseModel):
    site_id: str
    site_name: str
    substrate_type: str
    addr_street1: str
    addr_street2: Optional[str]
    addr_city: str
    addr_state: str
    addr_zip: int
    geom: object  # totally cheating here
    reports: Optional[List[ReportSchema]]
    reviews: Optional[List[ReviewSchema]]
    equipment: EquipmentSchema
    amenities: AmenitiesSchema
    sports_facilities: SportsFacilitiesSchema

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class UserSchema(BaseModel):
    email: str
    hashed_password: str
    first_name: str
    last_name: str
    favorite_parks: Optional[List[str]]

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class UserInDBSchema(UserSchema):
    email: str
    hashed_password: str
    first_name: str
    last_name: str
    favorite_parks: Optional[List[str]]


class UserResponseSchema(BaseModel):
    first_name: str
    last_name: str
    favorite_parks: Optional[List[str]]
    email: str

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class TokenSchema(BaseModel):
    access_token: str
    token_type: str


class TokenDataSchema(BaseModel):
    username: Optional[str] = None


class Globals:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "bearer"},
    )
    SECRET_KEY = os.environ.get("SECRET_KEY")
    ALGORITHM = os.environ.get("ALGORITHM")
    CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
    MILES_TO_METERS = 1609.34
