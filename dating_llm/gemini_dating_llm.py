import logging
import os
from typing import List, Any, Tuple, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types

from dating_llm.agent_utils import get_image_data, response_to_json
from dating_llm.dating_llm import DatingLLM
from dating_llm.decision_reponse import DecisionResponse


class GeminiDatingLLM(DatingLLM):
    model_list: List[str] = [
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
    ]

    def __init__(self, user_pref: str) -> None:
        super().__init__()
        self._user_pref: str = user_pref
        self._model_idx = 1
        load_dotenv()
        api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
        try:
            api_key2: Optional[str] = os.getenv("GEMINI_API_KEY2")
        except:
            api_key2 = None
        self.client: genai.Client = genai.Client(api_key=api_key)
        if api_key2:
            self.client2: genai.Client = genai.Client(api_key=api_key2)
        else:
            self.client2 = None

    def close(self) -> None:
        self.client.close()

    def run_llm(self, profile_bio: str, images_urls: List[str]) -> Tuple[DecisionResponse, int]:
        try:
            return self._run_llm(profile_bio, images_urls)
        except (genai.errors.ClientError, genai.errors.ServerError):
            print("Switching model and retrying...")
            # self._model_idx = (self._model_idx + 1) % len(self.model_list)
            if self.client2 is None:
                logging.info(f"Switched to model: {self.model_list[self._model_idx]}")
                self._model_idx = (self._model_idx + 1) % len(self.model_list)
            else:
                logging.info("Switched to second client")
                temp = self.client
                self.client = self.client2
                self.client2 = temp
        return self._run_llm(profile_bio, images_urls)

    def _run_llm(self, profile_bio: str, images_urls: List[str]) -> Tuple[DecisionResponse, int]:
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
            config=genai.types.GenerateContentConfig(
                temperature=0.75,
                # response_mime_type='application/json',
            )
        )

        if response.text is None:
            print("Empty response received, retrying...")
            # retry once
            response = self.client.models.generate_content(
                model=selected_model,
                contents=contents,
            )

        token_usage: int = response.usage_metadata.total_token_count
        return DecisionResponse(**response_to_json(response.text)), token_usage
