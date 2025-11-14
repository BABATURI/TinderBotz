import json
import os
from dataclasses import asdict
from typing import Dict, Any

from tinderbotz.helpers.geomatch import Geomatch


class StorageHelper:
    @staticmethod
    def store_match(match: Geomatch, directory: str, filename: str) -> None:
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
            json.dump(data, file, indent=4)
