import json
import os
from dataclasses import asdict
from typing import Dict, Any

from tinderbotz.helpers.geomatch import Geomatch


class StorageHelper:
    @staticmethod
    def store_match(match: Geomatch, directory: str, is_liked: bool) -> None:
        if not os.path.exists(directory):
            os.makedirs(directory)

        filepath: str = os.path.join(directory, f"{match.match_type}_{'liked' if is_liked else 'disliked'}.json")
        try:
            with open(filepath, "r", encoding='utf-8') as fp:
                data: Dict[str, Any] = json.load(fp)
        except IOError:
            print("Could not read file, starting from scratch")
            data = {}
        try:
            data[match.id] = asdict(match)
        except Exception as e:
            print(e)

        with open(filepath, 'w+', encoding="utf-8") as file:
            json.dump(data, file, indent=4)
