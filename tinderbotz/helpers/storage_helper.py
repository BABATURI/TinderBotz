import json
import os
from dataclasses import asdict
from typing import Dict, Any

from dating_llm.decision_reponse import DecisionResponse
from tinderbotz.helpers.geomatch import Geomatch
from tinderbotz.helpers.match_data import MatchData


class StorageHelper:
    @staticmethod
    def store_match(match: Geomatch, directory: str, decision: DecisionResponse) -> None:
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        filepath: str = os.path.join(directory, f"{match.match_type}_{'liked' if decision.is_like else 'disliked'}.json")
        try:
            with open(filepath, "r", encoding='utf-8') as fp:
                data: Dict[str, Any] = json.load(fp)
        except IOError:
            print("Could not read file, starting from scratch")
            data = {}
        try:
            match_json = asdict(match)
            match_json.update(asdict(decision))
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
        

    @staticmethod
    def load_matches_data(app_name: str) -> Dict[str, MatchData]:
        """
        Loads match data for a specific app.
        
        Args:
            app_name (str): The name of the app (e.g., 'okcupid', 'tinder').
            
        Returns:
            Dict[str, MatchData]: A dictionary of user_id -> MatchData.
        """
        directory = os.path.join("data", app_name)
        filepath = os.path.join(directory, "matches_data.json")
        if not os.path.exists(filepath):
            return {}
            
        try:
            with open(filepath, "r", encoding='utf-8') as fp:
                data = json.load(fp)
                return {k: MatchData.from_dict(v) for k, v in data.items()}
        except Exception as e:
            print(f"Error loading matches data: {e}")
            return {}

    @staticmethod
    def save_matches_data(app_name: str, data: Dict[str, MatchData]) -> None:
        """
        Saves match data for a specific app.
        
        Args:
            app_name (str): The name of the app.
            data (Dict[str, MatchData]): The data to save.
        """
        directory = os.path.join("data", app_name)
        if not os.path.exists(directory):
            os.makedirs(directory)
            
        filepath = os.path.join(directory, "matches_data.json")
        try:
            json_data = {k: v.to_dict() for k, v in data.items()}
            with open(filepath, 'w+', encoding="utf-8") as file:
                json.dump(json_data, file, indent=4)
        except Exception as e:
            print(f"Error saving matches data: {e}")
