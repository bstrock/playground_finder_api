from sqlalchemy.dialects.postgresql import ENUM
from dataclasses import dataclass

#  this dataclass allows enumeration value definition, and provides a .make() method which
#  generates a SQLAlchemy ENUM object based on the contents of the enum tuple.


@dataclass
class EnumStorage:
    report_types: tuple

    def make(self, kind):

        # give me a kind, I'll give you an attribute tuple
        obj = self.__getattribute__(kind)

        # nice tuple!  Here's an enumeration for your database.
        return ENUM(*obj, name=str(kind))


#  enum tuples
report_types = (
    "HAZARD",
    "LITTER",
    "OFFLEASH_DOG",
    "EQUIPMENT_ISSUE",
    "VANDALISM",
    "DAMAGE",
)

# instantiate- this object is imported in main script

enums = EnumStorage(report_types=report_types)
