import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

from dating_llm.agent_utils import response_to_json, get_image_data


class DatingLLM:
	prompt = """You are a dating assistant AI. your Job is to decide whether to like or dislike a profile based on the bio and images provided, and the user's preferences.
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

	def __init__(self, user_pref):
		self._user_pref = user_pref
		load_dotenv()
		api_key = os.getenv("GEMINI_API_KEY")
		self.client = genai.Client(api_key=api_key)

	def close(self):
		self.client.close()

	def __exit__(self):
		self.client.close()

	def run_llm(self, profile_bio, images_urls):
		user_prompt = self.prompt.format(
			user_preferences=self._user_pref,
			profile_info=profile_bio,
		)
		contents = [
			user_prompt
		]
		for img_url in images_urls:
			contents.append(types.Part.from_bytes(
				data=get_image_data(img_url),
				mime_type='image/jpeg',
			))
		response = self.client.models.generate_content(
			model="gemini-2.5-flash",
			contents=contents,
		)
		usage = response.usage_metadata
		token_usage = usage.total_token_count
		return response_to_json(response.text), token_usage
