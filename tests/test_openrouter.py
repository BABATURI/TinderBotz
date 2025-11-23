from openai import OpenAI
from dotenv import load_dotenv
from dating_llm.agent_utils import get_image_data
import base64
import os

PROMT_TEMPLATE: str = """You are a dating assistant AI. your Job is to decide whether to like or dislike a profile based on the bio and images provided, and the user's preferences.
Respond with 'like' or 'dislike' only.
The user prefrences are: {user_preferences}

Profile Info: {profile_info}

There are a few images for the profile, attached into the query.
The output should look like so: (new line after each field, only these fileds below):
```
decision: <like or dislike>
reason: <a brief explanation of the decision>
like_message: <first message in hebrew to send to the match. it should be a cheesy and funny pickup line
that shows you read the profile. do not add emojies, do not write the match's name.>
```
"""
USER_PREF = """I like women who:
- are fit and slim, with blonde / ginger / hazel hair and bright eyes.
- express interset in computers and engneering (not a must, but big bonus).
I do not like women:
- who smoke.

Filter out profiles with only instagram bio (aka super short bio with "ig" or "instagram" or "@" with her instagram name), empty bio is fine.
the match should have one of the following insterests:
- she enjoys outdoor activities
- she has a good sense of humor
- she is athletic and like sports
- she likes movies/video games
it's ok if she doesnt have a bio but you can infer from the pictures she has one of the above qualities."""

PROFILE_INFO = """
"name": "Debbie",
        "age": 21,
        "work": null,
        "study": null,
        "home": "Ra`ananna",
        "gender": null,
        "bio": "Buscando an\u00e9cdotas.",
        "lifestyle": "Drinks sometimes",
        "basics": "Woman | Straight | Monogamous (Single)",
        "looking_for": "Looking for Men | Long-term dating",
        "distance": null,
        "passions": "",
        "instagram": null,
        "image_urls": [
            "https://pictures.match.com/photos/060/418/3374e192-e6bb-f011-9b70-6c92cf29d881.jpeg",
            "https://pictures.match.com/photos/060/418/26f59d02-e6bb-f011-9b70-6c92cf29d881.jpeg",
            "https://pictures.match.com/photos/060/418/4663fe50-e6bb-f011-9b70-6c92cf29d881.jpeg",
            "https://pictures.match.com/photos/060/418/e650d24d-e7bb-f011-9b70-6c92cf29d881.jpeg",
            "https://pictures.match.com/photos/060/418/e1aeecbf-e7bb-f011-9b70-6c92cf29d881.jpeg",
            "https://pictures.match.com/photos/060/418/73ef5369-e8bb-f011-9b70-6c92cf29d881.jpeg",
            "https://pictures.match.com/photos/060/418/5b04661e-ebbb-f011-9b70-6c92cf29d881.jpeg",
            "https://pictures.match.com/photos/060/418/57727930-ebbb-f011-9b70-6c92cf29d881.jpeg"
        ],
        "listening": [],
        "prompts": []
"""
image_urls = ["https://pictures.match.com/photos/060/418/3374e192-e6bb-f011-9b70-6c92cf29d881.jpeg",
            "https://pictures.match.com/photos/060/418/26f59d02-e6bb-f011-9b70-6c92cf29d881.jpeg",
            "https://pictures.match.com/photos/060/418/4663fe50-e6bb-f011-9b70-6c92cf29d881.jpeg",
            "https://pictures.match.com/photos/060/418/e650d24d-e7bb-f011-9b70-6c92cf29d881.jpeg",
            "https://pictures.match.com/photos/060/418/e1aeecbf-e7bb-f011-9b70-6c92cf29d881.jpeg",
            "https://pictures.match.com/photos/060/418/73ef5369-e8bb-f011-9b70-6c92cf29d881.jpeg",
            "https://pictures.match.com/photos/060/418/5b04661e-ebbb-f011-9b70-6c92cf29d881.jpeg",
            "https://pictures.match.com/photos/060/418/57727930-ebbb-f011-9b70-6c92cf29d881.jpeg"]

PROFILE_INFO2 = """
        "name": "Tali",
        "age": 23,
        "work": null,
        "study": null,
        "home": "Ramat Gan",
        "gender": null,
        "bio": "hi you",
        "lifestyle": "Doesn't smoke cigarettes | Drinks sometimes | Never smokes marijuana",
        "basics": "Woman | Straight | Monogamous (Single)",
        "looking_for": "Looking for Men | Long-term dating",
        "distance": null,
        "passions": "",
        "instagram": null,
        "image_urls": [
            "https://pictures.match.com/photos/301/123/14848319-63f1-ef11-9b67-6c92cf29d881.jpeg",
            "https://pictures.match.com/photos/301/123/e9c85bac-5af1-ef11-9b67-6c92cf29d881.jpeg",
            "https://pictures.match.com/photos/301/123/1bad1666-1116-f011-8034-6c92cf29dc01.jpeg",
            "https://pictures.match.com/photos/301/123/7a1787d0-5af1-ef11-9b67-6c92cf29d881.jpeg",
            "https://pictures.match.com/photos/301/123/0789cee8-10e3-ef11-8032-6c92cf29dc01.jpeg",
            "https://pictures.match.com/photos/301/123/af940d73-11e3-ef11-8032-6c92cf29dc01.jpeg"
        ],
        "listening": [],
        "prompts": [],
"""

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=api_key,
)

image_urls2 = ["https://pictures.match.com/photos/301/123/14848319-63f1-ef11-9b67-6c92cf29d881.jpeg",
            "https://pictures.match.com/photos/301/123/e9c85bac-5af1-ef11-9b67-6c92cf29d881.jpeg",
            "https://pictures.match.com/photos/301/123/1bad1666-1116-f011-8034-6c92cf29dc01.jpeg",
            "https://pictures.match.com/photos/301/123/7a1787d0-5af1-ef11-9b67-6c92cf29d881.jpeg",
            "https://pictures.match.com/photos/301/123/0789cee8-10e3-ef11-8032-6c92cf29dc01.jpeg",
            "https://pictures.match.com/photos/301/123/af940d73-11e3-ef11-8032-6c92cf29dc01.jpeg"]

content = [{"type": "text", "text": PROMT_TEMPLATE.format(
                user_preferences=USER_PREF, profile_info=PROFILE_INFO)}]

for url in image_urls:
    data = get_image_data(url)
    i = f"data:image/jpeg;base64,{base64.b64encode(data)}"           
    content.append({"type": "image_url", "image_url": {"url": i,},})

MODEL = "x-ai/grok-4.1-fast"
# MODEL = "mistralai/mistral-small-3.2-24b-instruct:free"  # ok but slow AF

# MODEL = "google/gemma-3-12b-it:free"

completion = client.chat.completions.create(
  model=MODEL,
  messages=[
    {
        "role": "user",
        "content": content
    }
  ],
  response_format={"type": "json_object"}
)
print(completion.choices[0].message.content)

content = [{"type": "text", "text": PROMT_TEMPLATE.format(
                user_preferences=USER_PREF, profile_info=PROFILE_INFO2)}]

for url in image_urls2:
    data = get_image_data(url)
    i = f"data:image/jpeg;base64,{base64.b64encode(data)}"
                    
    content.append({"type": "image_url", "image_url": {"url": url}})


completion = client.chat.completions.create(
  model=MODEL,
  messages=[
    {
        "role": "user",
        "content": content
    },
  ],
  response_format={"type": "json_object"}
)
print(completion.choices[0].message.content)