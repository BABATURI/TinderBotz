import json
import time
import traceback
from pathlib import Path
from datetime import datetime
from dataclasses import asdict

from tinderbotz.base_session import BaseSession
from tinderbotz.bumble_session import BumbleSession
from tinderbotz.okcupid_session import OkCupidSession
from tinderbotz.helpers.bot_settings import BotSettings
from tinderbotz.tinder_session import TinderSession, Geomatch
from dating_llm.agent import *


def __sleep_until(hour: int, minute: int) -> None:
    now = datetime.datetime.now()
    target_time = datetime.datetime(now.year, now.month, now.day, hour, minute)

    # If the target time is in the past, set it for the next day
    if now > target_time:
        target_time += datetime.timedelta(days=1)
    else:
        return

    sleep_duration = (target_time - now).total_seconds()

    time.sleep(sleep_duration)


def __create_dating_agent() -> DatingLLM:
    config_file: Path = Path("configuration", "user_pref")

    user_pref: str = "I like fit and slim, blonde / hazel haired women with bright eyes who enjoy outdoor activities and have a good sense of humor."
    if config_file.exists():
        with open("configuration/user_pref", "r") as f:
            user_pref = f.read()

    return DatingLLM(user_pref)


def __load_bot_settings() -> BotSettings:
    settings_path = Path("configuration", "bot_settings.json")
    if settings_path.exists():
        with open(settings_path, "r") as f:
            return BotSettings(**json.load(f))
    else:
        # create default settings file
        default_settings = BotSettings()
        with open(settings_path, "w") as f:
            json.dump(asdict(default_settings), f, indent=4)
        return default_settings


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


def __perform_round(unentered_base_session: BaseSession, settings: BotSettings) -> None:
    max_likes = settings.max_likes_per_session
    max_swipes = settings.max_swipes_per_session
    
    with unentered_base_session as session:
        location: Tuple[float, float] = settings.location
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
    settings = __load_bot_settings()
    sessions = [
        # BumbleSession(),
        # TinderSession(),
        OkCupidSession(),
    ]
    while True:
        if datetime.now().hour < settings.active_hours_start:
            __sleep_until(settings.active_hours_start, 0)
            
        elif datetime.now().hour >= settings.active_hours_end:
            # sleep until the next day, then start again
            __sleep_until(23, 59)
            time.sleep(61)
            continue

        for session in sessions:
            try:
                __perform_round(session, settings)
            except Exception as e:
                print(f"got exception {e}")
                traceback.print_exc()

        print("Sleeping till next session")
        time.sleep(settings.sleep_time)


if __name__ == "__main__":
    main()
