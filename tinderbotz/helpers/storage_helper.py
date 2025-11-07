import json
import os
import random
import string

from dataclasses import asdict
from typing import Dict, Any

from tinderbotz.helpers.geomatch import Geomatch


class StorageHelper:
	@staticmethod
	def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
		return ''.join(random.choice(chars) for _ in range(size))

	# Returns hash value of the image saved by the url given
	@staticmethod
	def store_image_as(image: bytes, directory):
		if not os.path.exists(directory):
			os.makedirs(directory)

		temp_name = "temporary"

		with open("{}/{}/{}.png".format(os.getcwd(), directory, temp_name), 'wb') as f:
			f.write(image)

	@staticmethod
	def store_json(match: Geomatch, directory: str, filename: str) -> None:
		if not os.path.exists(directory):
			os.makedirs(directory)

		filepath: str = os.path.join(directory, f"{filename}.json")
		try:
			with open(filepath, "r", encoding='utf-8') as fp:
				data: Dict[str, Any] = json.load(fp)
		except IOError:
			print("Could not read file, starting from scratch")
			data = {}

		data[match.id] = asdict(match)
		with open(filepath, 'w+', encoding="utf-8") as file:
			json.dump(data, file)
