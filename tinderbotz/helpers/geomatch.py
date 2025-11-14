import json
import random
import string
from dataclasses import asdict, dataclass, field
from typing import Any, List, Optional, Dict


@dataclass
class Geomatch:
    name: Optional[str] = None
    age: Optional[int] = None
    work: Optional[str] = None
    study: Optional[str] = None
    home: Optional[str] = None
    gender: Optional[str] = None
    bio: Optional[str] = None
    lifestyle: Optional[str] = None
    basics: Optional[str] = None
    looking_for: Optional[str] = None
    distance: Optional[float] = None
    passions: Optional[str] = None
    instagram: Optional[str] = None
    image_urls: List[str] = field(default_factory=list)
    listening: List[Any] = field(default_factory=list)
    prompts: Dict[str, str] = field(default_factory=list)
    id: str = field(init=False)

    @property
    def match_type(self) -> str:
        return "geomatch"

    def __post_init__(self) -> None:
        self.gen_id()

    def gen_id(self):
        random_id: str = ''.join(random.choice(string.ascii_uppercase + string.digits)
                                 for _ in range(6))
        self.id = "{}{}_{}".format(self.name, self.age, random_id)

    def __str__(self):
        return f"{json.dumps({x: y for x, y in asdict(self).items() if y not in (None, '', [])}, indent=4)}"
