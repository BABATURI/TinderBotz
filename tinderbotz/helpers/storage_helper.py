import json
import os
from dataclasses import asdict
from typing import Dict, Any

from tinderbotz.helpers.geomatch import Geomatch


class StorageHelper:
    @staticmethod
    def store_match(match: Geomatch, directory: str, des_json: Dict[str, str]) -> None:
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        is_liked: bool = des_json["decision"] == "like"
        filepath: str = os.path.join(directory, f"{match.match_type}_{'liked' if is_liked else 'disliked'}.json")
        try:
            with open(filepath, "r", encoding='utf-8') as fp:
                data: Dict[str, Any] = json.load(fp)
        except IOError:
            print("Could not read file, starting from scratch")
            data = {}
        try:
            match_json = asdict(match)
            match_json.update(des_json)
            data[match.id] = match_json
        except Exception as e:
            print(e)

        with open(filepath, 'w+', encoding="utf-8") as file:
            json.dump(data, file, indent=4)
    
    @staticmethod
    def load_match(match_id: str, directory: str, decision: str) -> Geomatch:
        """
        Loads a match by ID from the appropriate file.

        Args:
            match_id (str): The ID of the match to load.
            directory (str): The directory where match files are stored.
            decision (str): 'like' or 'dislike' (used in filename).

        Returns:
            Geomatch: The loaded Geomatch object, or None if not found.
        """
        match_type = "geomatch"
        filename = f"{match_type}_{'liked' if decision == 'like' else 'disliked'}.json"
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, "r", encoding='utf-8') as fp:
                data = json.load(fp)
            match_data = data.get(match_id)
            if match_data:
                return Geomatch(**{k: v for k, v in match_data.items() if k in Geomatch.__dataclass_fields__})
        except Exception as e:
            print(f"Error loading match: {e}")
        return None
        
