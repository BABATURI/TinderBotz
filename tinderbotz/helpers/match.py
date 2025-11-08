from dataclasses import dataclass
from typing import Optional

from tinderbotz.helpers.geomatch import Geomatch


# A match has the same information as a geomatch, except that you have a chatroom with an id
@dataclass
class Match(Geomatch):
    chatid: Optional[str] = None

    @property
    def match_type(self) -> str:
        return "match"
