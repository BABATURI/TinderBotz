import random
import string
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class Geomatch:
	name: Optional[str]
	age: Optional[int]
	work: Optional[str]
	study: Optional[str]
	home: Optional[str]
	gender: str
	bio: Optional[str]
	lifestyle: Optional[str] = None
	basics: Optional[str] = None
	anthem: Optional[str] = None
	looking_for: Optional[str] = None
	distance: Optional[float] = None
	passions: Optional[str] = None
	instagram: Optional[str] = None
	image_urls: List[str] = field(default_factory=list)
	prompts: List[Any] = field(default_factory=list)
	listening: List[Any] = field(default_factory=list)
	id: str = field(init=False)

	def __post_init__(self) -> None:
		random_id: str = ''.join(random.choice(string.ascii_uppercase + string.digits)
		                         for _ in range(6))

		self.id = "{}{}_{}".format(self.name, self.age, random_id)
