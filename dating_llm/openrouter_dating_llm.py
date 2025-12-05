import json
import logging
import os
from typing import List, Tuple, Optional

import openai
from dotenv import load_dotenv
from openai import OpenAI

from dating_llm.dating_llm import DatingLLM
from dating_llm.agent_utils import response_to_json
from dating_llm.decision_reponse import DecisionResponse


class OpenRouterDatingLLM(DatingLLM):
    model_list: List[str] = [
                            "amazon/nova-2-lite-v1:free",
                            # "x-ai/grok-4.1-fast",
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

    def run_llm(self, profile_bio: str, images_urls: List[str]) -> Tuple[DecisionResponse, int]:
        try:
            return self._run_llm(profile_bio, images_urls)
        except (openai.APITimeoutError, openai.RateLimitError):
            print("Switching model and retrying...")
            self._model_idx = (self._model_idx + 1) % len(self.model_list)
            logging.info(f"Switched to model: {self.model_list[self._model_idx]}")
        return self._run_llm(profile_bio, images_urls)

    def _run_llm(self, profile_bio: str, images_urls: List[str]) -> Tuple[DecisionResponse, int]:
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
            
        logging.info(text)
        return self._parse_response(text), token_usage

    def _parse_response(self, response: str) -> DecisionResponse:
        try:
            return DecisionResponse(**json.loads(response))
        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"Failed to parse response: {e}")
        # fallback to line by line text parsing
        return DecisionResponse(**response_to_json(response))
                