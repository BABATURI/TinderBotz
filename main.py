import json
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from tinderbotz.session import Session, Geomatch
from dating_llm.agent import *


def __create_dating_agent() -> DatingLLM:
    config_file: Path = Path("configuration", "user_pref")

    user_pref: str = "I like fit and slim, blonde / hazel haired women with bright eyes who enjoy outdoor activities and have a good sense of humor."
    if config_file.exists():
        with open("configuration/user_pref", "r") as f:
            user_pref = f.read()

    return DatingLLM(user_pref)


def __get_response_from_dating_agent(dllm: DatingLLM, geomatch: Geomatch) -> Dict[str, Any]:
    # Note: to save tokens we don't save everything - only what matters
    minimized_duplicate_geomatch: Geomatch = Geomatch(name=geomatch.name,
                                                      age=geomatch.age,
                                                      work=geomatch.work,
                                                      study=geomatch.study,
                                                      bio=geomatch.bio,
                                                      lifestyle=geomatch.lifestyle,
                                                      passions=geomatch.passions,
                                                      looking_for=geomatch.looking_for)

    query: str = (f"Full profile info:\n"
                  f"{json.dumps({x: y for x, y in asdict(minimized_duplicate_geomatch).items() if y not in (None, '', [])}, indent=4)}")
    image_urls: List[str] = geomatch.image_urls[:3]

    ai_json_response, total_tokens = dllm.run_llm(query, image_urls)
    print(f"Total tokens used: {total_tokens}")
    return ai_json_response


def __perform_round(max_likes: int = 30, max_swipes: int = 60) -> None:
    with Session() as session:
        location: Tuple[float, float] = (32.15792931573261, 34.84213125060156)
        session.set_custom_location(latitude=location[0], longitude=location[1])

        session.wait_for_login()

        dating_agent: DatingLLM = __create_dating_agent()

        likes_cnt: int = 0

        for _ in range(max_swipes):
            # get profile data (name, age, bio, images, ...)
            geomatch: Geomatch = session.get_geomatch()
            # store this data locally as json with reference to their respective (locally stored) images
            session.store_local(geomatch)
            # Use the dating agent to decide whether to like or dislike this profile
            print("running dating LLM query...")
            decision_json: Dict[str, Any] = __get_response_from_dating_agent(dating_agent, geomatch)

            print(f"Decision for {geomatch.name}, age {geomatch.age}:\n{decision_json}")
            if decision_json["decision"] == "like":
                session.like()
                likes_cnt += 1
            else:
                session.dislike()

            if likes_cnt == max_likes:
                return


def main() -> None:
    # todo- handle no more likes left/no options are left
    while True:
        MIN_HOUR_FOR_SWIPING: int = 10

        if datetime.now().hour < MIN_HOUR_FOR_SWIPING:
            time.sleep(MIN_HOUR_FOR_SWIPING - datetime.now().hour)

        try:
            __perform_round(1, 3)
        except Exception as e:
            print(f"got exception {e}")

        print("Sleeping till next session")
        ONE_HOUR_IN_SECS: int = 60 * 60
        time.sleep(ONE_HOUR_IN_SECS)


if __name__ == "__main__":
    main()
