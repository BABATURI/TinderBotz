import json
import os
import random
import string
from typing import Any, Dict, List, Optional


def _id_generator(size: int = 6, chars: str = string.ascii_uppercase + string.digits) -> str:
	return ''.join(random.choice(chars) for _ in range(size))


class Geomatch:
	def __init__(
		self,
		name: str,
		age: Optional[int],
		work: Optional[str],
		study: Optional[str],
		home: Optional[str],
		gender: str,
		bio: Optional[str],
		lifestyle: Optional[Dict[str, Any]],
		basics: Optional[Dict[str, Any]],
		anthem: Optional[str],
		looking_for: Optional[str] = None,
		distance: Optional[float] = None,
		passions: Optional[List[str]] = None,
		instagram: Optional[str] = None,
		images: Optional[List[str]] = None,
	) -> None:
		self.name: str = name
		self.age: Optional[int] = age
		self.work: Optional[str] = work
		self.study: Optional[str] = study
		self.home: Optional[str] = home
		self.gender: str = gender
		self.passions: Optional[List[str]] = passions
		self.bio: Optional[str] = bio
		self.lifestyle: Optional[Dict[str, Any]] = lifestyle
		self.basics: Optional[Dict[str, Any]] = basics
		self.anthem: Optional[str] = anthem
		self.looking_for: Optional[str] = looking_for
		self.distance: Optional[float] = distance
		self.images: List[str] = images or []
		self.instagram: Optional[str] = instagram
		self.prompts: List[Any] = []
		self.listening: List[Any] = []

		self.id: str = "{}{}_{}".format(name, age, _id_generator(size=4))

	def get_name(self) -> str:
		return self.name

	def get_age(self) -> Optional[int]:
		return self.age

	def get_work(self) -> Optional[str]:
		return self.work

	def get_study(self) -> Optional[str]:
		return self.study

	def get_home(self) -> Optional[str]:
		return self.home

	def get_gender(self) -> str:
		return self.gender

	def get_passions(self) -> Optional[List[str]]:
		return self.passions

	def get_bio(self) -> Optional[str]:
		return self.bio

	def get_lifestyle(self) -> Optional[Dict[str, Any]]:
		return self.lifestyle

	def get_basics(self) -> Optional[Dict[str, Any]]:
		return self.basics

	def get_anthem(self) -> Optional[str]:
		return self.anthem

	def get_looking_for(self) -> Optional[str]:
		return self.looking_for

	def get_distance(self) -> Optional[float]:
		return self.distance

	def get_instagram(self) -> Optional[str]:
		return self.instagram

	def get_id(self) -> str:
		return self.id

	def get_dictionary(self) -> Dict[str, Any]:
		data: Dict[str, Any] = {
			"name": self.get_name(),
			"age": self.get_age(),
			"work": self.get_work(),
			"study": self.get_study(),
			"home": self.get_home(),
			"gender": self.gender,
			"bio": self.get_bio(),
			"distance": self.get_distance(),
			"basics": self.get_basics(),
			"lifestyle": self.get_lifestyle(),
			"passions": self.get_passions(),
			"anthem": self.get_anthem(),
			"looking_for": self.get_looking_for(),
			"instagram": self.get_instagram(),
			"images": self.images,
		}
		return data

	def store_json(self, directory: str, filename: str) -> None:
		if not os.path.exists(directory):
			os.makedirs(directory)

		filepath: str = os.path.join(directory, f"{filename}.json")
		try:
			with open(filepath, "r", encoding='utf-8') as fp:
				data: Dict[str, Any] = json.load(fp)
		except IOError:
			print("Could not read file, starting from scratch")
			data = {}

		data[self.get_id()] = self.get_dictionary()
		with open(filepath, 'w+', encoding="utf-8") as file:
			json.dump(data, file)
