from typing import List, Dict, Any, Tuple


# todo: moved shared logic
class DatingLLM:
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
    like_message: (if you like the profile) <first message in hebrew to send to the match. she is a girl. it should be a cheesy and funny pickup line
    that shows you read the profile. do not add emojies, do not write the match's name. don't make it over sexual.
    Write something engaging that she'll want to reply to.>

    Profile Info:
    ```
    {profile_info}
    ```
    There are a few images for the profile, attached into the query.
    """
    def __init__(self) -> None:
        pass

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def close(self) -> None:
        raise NotImplementedError()

    def run_llm(self, profile_bio: str, images_urls: List[str]) -> Tuple[Dict[str, Any], int]:
        raise NotImplementedError()
