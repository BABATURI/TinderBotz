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
    The output should look like so: (new line after each field, only these fileds below):
    ```
    decision: <like or dislike>
    reason: <a brief explanation of the decision>
    like_message: <first message in hebrew to send to the match. it should be a cheesy and funny pickup line that shows you read the profile>
    ```
    """
    model_list: List[str] = [
                            "gemini-2.5-pro",
                            "gemini-2.5-flash",
                            "gemini-2.0-flash",
                            "gemini-2.5-flash-lite",
                            "gemini-2.0-flash-lite",
                            ]
    
    def __init__(self, user_pref: str) -> None:
        self._user_pref: str = user_pref
        self._model_idx = 1
        load_dotenv()
        api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
        self.client: genai.Client = genai.Client(api_key=api_key)

    def close(self) -> None:
        self.client.close()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.client.close()

    def run_llm(self, profile_bio: str, images_urls: List[str]) -> Tuple[Dict[str, Any], int]:
        try:
            return self._run_llm(profile_bio, images_urls)
        except (genai.errors.ClientError, genai.errors.ServerError):
            print("Switching model and retrying...")
            self._model_idx = (self._model_idx + 1) % len(self.model_list)
        return self._run_llm(profile_bio, images_urls)

    def _run_llm(self, profile_bio: str, images_urls: List[str]) -> Tuple[Dict[str, Any], int]:
        selected_model: str = self.model_list[self._model_idx]  # Using "gemini-2.5-flash" as default for now

        user_prompt: str = self.PROMT_TEMPLATE.format(
            user_preferences=self._user_pref,
            profile_info=profile_bio,
        )

        contents: List[Any] = [user_prompt]

        for img_url in images_urls:
            img_data = get_image_data(img_url)
            if img_data == b'':
                continue

            contents.append(
                types.Part.from_bytes(
                    data=img_data,
                    mime_type="image/jpeg",
                )
            )
        
        response = self.client.models.generate_content(
            model=selected_model,
            contents=contents,
        )

        if response.text is None:
            print("Empty response received, retrying...")
            # retry once
            response = self.client.models.generate_content(
            model=selected_model,
            contents=contents,
            )

        token_usage: int = response.usage_metadata.total_token_count
        # TODO: fix empty response issue
        print(">>>", response.text, "<<<")
        return response_to_json(response.text), token_usage
