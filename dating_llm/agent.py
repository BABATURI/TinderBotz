import os
import io
import json
import requests

from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv


def _get_image_data(url):
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    orig_bytes = resp.content

    try:
        img = Image.open(io.BytesIO(orig_bytes))
        # Resize if larger than max dimension
        max_dim = 1024
        if max(img.size) > max_dim:
            ratio = max_dim / max(img.size)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        out = io.BytesIO()
        # Preserve alpha by using PNG, otherwise compress to JPEG
        
        img = img.convert("RGB")
        img.save(out, format="JPEG", quality=70, optimize=True, progressive=True)

        img_data = out.getvalue()
        out.close()
    except Exception:
        # On failure, fall back to original bytes
        img_data = orig_bytes
    return img_data


def _response_to_json(text):
    if not isinstance(text, str):
        text = str(text)
    start_marker = "```json"
    end_marker = "```"
    start = text.find(start_marker)
    if start == -1:
        raise ValueError("No '```json' block found in response")
    start += len(start_marker)
    end = text.find(end_marker, start)
    if end == -1:
        raise ValueError("No closing '```' found for JSON block")
    json_str = text[start:end].strip()
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        try:
            return json.loads(json_str.replace("'", '"'))
        except Exception:
            raise ValueError("Failed to parse JSON from code block") from e


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
                data=_get_image_data(img_url),
                mime_type='image/jpeg',
            ))
        response = self.client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        )
        usage = response.usage_metadata
        token_usage = usage.total_token_count
        return _response_to_json(response.text), token_usage
