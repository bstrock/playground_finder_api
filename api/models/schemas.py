from typing import Optional, Any

from pydantic import BaseModel


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
    splash_pad: Optional[int]
    beach: Optional[int]
    changing_rooms: Optional[int]
    waterfront: Optional[int]
    concessions: Optional[int]
    rentals: Optional[int]
    indoor_restroom: Optional[int]
    portable_restroom: Optional[int]
    picnic_tables: Optional[int]
    benches: Optional[int]
    shelter: Optional[int]
    sun_shades: Optional[int]
    grills: Optional[int]

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class SportsFacilitiesSchema(BaseModel):
    skate_park: Optional[int]
    disc_golf: Optional[int]
    foursquare: Optional[int]
    badminton: Optional[int]
    tennis_court: Optional[int]
    hockey_rink: Optional[int]
    soccer_field: Optional[int]
    basketball_court: Optional[int]
    baseball_diamond: Optional[int]
    volleyball: Optional[int]
    horseshoes: Optional[int]

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class SiteSchema(BaseModel):
    site_id: str
    site_name: str
    addr_street1: str
    addr_street2: Optional[str]
    addr_city: str
    addr_state: str
    addr_zip: int
    geom: Any  # totally cheating here
    equipment: EquipmentSchema
    amenities: AmenitiesSchema
    sports_facilities: SportsFacilitiesSchema

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True
