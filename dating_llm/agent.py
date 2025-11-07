import os
from typing import List, Dict, Any, Tuple, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types

from dating_llm.agent_utils import response_to_json, get_image_data


class DatingLLM:
	PROMT_TEMPLATE: str = """You are a dating assistant AI. your Job is to decide whether to like or dislike a profile based on the bio and images provided, and the user's preferences.
    Respond with 'like' or 'dislike' only.
    The user prefrences are" {user_preferences}
    Profile Info: {profile_info}
    There are a few images for the profile, attached into the query.
    The output should be a JSON object with the following fields:
    {{
        "decision": "like" or "dislike",
        "reason": "a brief explanation of the decision"
    }}
    """

	def __init__(self, user_pref: str) -> None:
		self._user_pref: str = user_pref
		load_dotenv()
		api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
		self.client: genai.Client = genai.Client(api_key=api_key)

	def close(self) -> None:
		self.client.close()

	def __exit__(self, exc_type, exc_val, exc_tb) -> None:
		self.client.close()

	def run_llm(self, profile_bio: str, images_urls: List[str]) -> Tuple[Dict[str, Any], int]:
		user_prompt: str = self.PROMT_TEMPLATE.format(
			user_preferences=self._user_pref,
			profile_info=profile_bio,
		)

		contents: List[Any] = [user_prompt]

		for img_url in images_urls:
			contents.append(
				types.Part.from_bytes(
					data=get_image_data(img_url),
					mime_type="image/jpeg",
				)
			)

		response = self.client.models.generate_content(
			model="gemini-2.5-flash",
			contents=contents,
		)

		token_usage: int = response.usage_metadata.total_token_count

		return response_to_json(response.text), token_usage
