import json
import logging
import os
from typing import List, Dict, Any, Tuple, Optional

import openai
from dotenv import load_dotenv
from openai import OpenAI

from dating_llm.dating_llm import DatingLLM


class OpenRouterDatingLLM(DatingLLM):
    PROMT_TEMPLATE: str = """
    You are a dating assistant AI. your Job is to decide whether to like or dislike a profile based on the bio and images provided, and the user's preferences.
    Respond with 'like' or 'dislike' only.
    The user prefrences are:
    ```md
    {user_preferences}
    ```
    The output should look like so: (new line after each field, only these fileds below):
    decision: <like or dislike>
    reason: <a brief explanation of the decision>
    like_message: <first message in hebrew to send to the match. she is a girl. it should be a cheesy and funny pickup line
    that shows you read the profile. do not add emojies, do not write the match's name. don't make it over sexual.>

    Profile Info:
    ```
    {profile_info}
    ```
    There are a few images for the profile, attached into the query.
    """
    model_list: List[str] = [
                            "x-ai/grok-4.1-fast",
                            ]
    
    def __init__(self, user_pref: str) -> None:
        super().__init__()
        self._user_pref: str = user_pref
        self._model_idx = 0
        load_dotenv()
        api_key: Optional[str] = os.getenv("OPENROUTER_API_KEY")
        self.client: OpenAI = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

    def close(self) -> None:
        self.client.close()

    def run_llm(self, profile_bio: str, images_urls: List[str]) -> Tuple[Dict[str, Any], int]:
        try:
            return self._run_llm(profile_bio, images_urls)
        except (openai.APITimeoutError, openai.RateLimitError):
            print("Switching model and retrying...")
            self._model_idx = (self._model_idx + 1) % len(self.model_list)
            logging.info(f"Switched to model: {self.model_list[self._model_idx]}")
        return self._run_llm(profile_bio, images_urls)

    def _run_llm(self, profile_bio: str, images_urls: List[str]) -> Tuple[Dict[str, Any], int]:
        selected_model: str = self.model_list[self._model_idx]

        user_prompt: str = self.PROMT_TEMPLATE.format(
            user_preferences=self._user_pref,
            profile_info=profile_bio,
        )

        contents = [{"type": "text", "text": user_prompt}]

        for img_url in images_urls:
            contents.append({"type": "image_url", "image_url": {"url": img_url,},})

        completion = self.client.chat.completions.create(
            model=selected_model,
            messages=[
                {
                    "role": "user",
                    "content": contents
                }
            ],
            response_format={"type": "json_object"}
        )
        text = completion.choices[0].message.content
        token_usage: int = completion.usage.total_tokens
        if text is None:
            print("Empty response received, retrying...")
            # retry once
            completion = self.client.chat.completions.create(
                model=selected_model,
                messages=[
                    {
                        "role": "user",
                        "content": contents
                    }
                ],
                response_format={"type": "json_object"}
            )
            text = completion.choices[0].message.content
            token_usage: int = completion.usage.total_tokens
        return json.loads(text), token_usage
