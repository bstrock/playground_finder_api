import dataclasses
from dataclasses import dataclass
import json


@dataclass
class TRISite:
    id: str
    name: str
    address: str
    city: str
    county: str
    state: str
    zip: int
    latitude: float
    longitude: float
    sector: str
    chemicals: dict
    carcinogen: bool

    def to_json(self):
        return json.dumps(dataclasses.asdict(self))