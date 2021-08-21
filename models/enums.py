from sqlalchemy.dialects.postgresql import ENUM
from dataclasses import dataclass

#  this dataclass allows enumeration value definition, and provides a .make() method which
#  generates a SQLAlchemy ENUM object based on the contents of the enum tuple.
@dataclass
class EnumStorage:
    report_types: tuple
    emission_types: tuple
    activity_types: tuple
    unused_types: tuple
    industry_sectors: tuple

    def make(self, kind):

        # give me a kind, I'll give you an attribute tuple
        obj = self.__getattribute__(kind)

        # nice tuple!  Here's an enumeration for your database.
        return ENUM(*obj, name=str(kind))


#  enum tuples
report_types = ("Active Site", "Emission", "Inactive Site")
emission_types = ("Water", "Air", "Land")
activity_types = ("Sitework", "Manufacturing", "Logistics")
unused_types = ("Signage", "Lack of Activity", "Disrepair")
industry_sectors = (
    "Machinery",
    "Wood Products",
    "Primary Metals",
    "Petroleum",
    "Fabricated Metals",
    "Computers and Electronic Products",
    "Food",
    "Electric Utilities",
    "Miscellaneous Manufacturing",
    "Chemicals",
    "Transportation Equipment",
    "Nonmetallic Mineral Product",
    "Electrical Equipment",
    "Plastics and Rubber",
    "Hazardous Waste",
    "Other",
    "Chemical Wholesalers",
    "Petroleum Bulk Terminals",
    "Furniture",
    "Printing",
    "Paper",
    "Leather",
)

# instantiate- this object is imported in main script

enums = EnumStorage(
    report_types=report_types,
    emission_types=emission_types,
    activity_types=activity_types,
    unused_types=unused_types,
    industry_sectors=industry_sectors,
)
