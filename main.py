import json
import logging
import time
import traceback
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from dating_llm.agent import *
from dating_llm.openrouter_agent import ORDatingLLM
from tinderbotz.base_session import BaseSession
from tinderbotz.bumble_session import BumbleSession
from tinderbotz.helpers.bot_settings import BotSettings
from tinderbotz.helpers.storage_helper import StorageHelper
from tinderbotz.okcupid_session import OkCupidSession
from tinderbotz.tinder_session import Geomatch, TinderSession


TRY_MESSAGE_BACK = True


def __create_dating_agent() -> DatingLLM:
    config_file: Path = Path("configuration", "user_pref.txt")

    user_pref: str = "I like fit and slim, blonde / hazel haired women with bright eyes who enjoy outdoor activities and have a good sense of humor."
    if config_file.exists():
        with open(config_file, "r") as f:
            user_pref = f.read()
    else:
        print("Creating default user preference file...")
        with open(config_file, "w") as f:
            f.write(user_pref)

    return ORDatingLLM(user_pref)


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


def __get_response_from_dating_agent(dllm: DatingLLM, settings: BotSettings, geomatch: Geomatch) -> Dict[str, Any]:
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
    image_urls: List[str] = geomatch.image_urls[:settings.image_count_to_use]

    ai_json_response, total_tokens = dllm.run_llm(query, image_urls)
    print(f"Total tokens used: {total_tokens}")
    return ai_json_response


def __perform_round(active_session: BaseSession, settings: BotSettings) -> None:
    max_likes = settings.max_likes_per_session
    max_swipes = settings.max_swipes_per_session

    location: Tuple[float, float] = settings.location
    active_session.set_custom_location(latitude=location[0], longitude=location[1])

    active_session.wait_for_login()

    dating_agent: DatingLLM = __create_dating_agent()

    likes_cnt: int = 0

    for _ in range(max_swipes):
        geomatch: Geomatch = active_session.get_geomatch()

        print("running dating LLM query...")
        decision_json: Dict[str, Any] = __get_response_from_dating_agent(dating_agent, settings, geomatch)

        print(f"Decision for {geomatch.name}, age {geomatch.age}:\n{decision_json}")
        if decision_json.get("decision", "") not in ("like", "dislike"):
            active_session.browser.refresh()
            time.sleep(5)
            continue

        GEOMATCHES_STORAGE_DIR: str = os.path.join(Path(os.path.abspath(__file__)).parent, "data")
        StorageHelper.store_match(geomatch, GEOMATCHES_STORAGE_DIR, decision_json)

        if decision_json["decision"] == "dislike":
            active_session.dislike()
        elif decision_json["decision"] == "like":
            active_session.like(
                message=decision_json.get("like_message", "") if active_session.does_support_message_on_like else None)
            likes_cnt += 1
        else:
            pass

        if likes_cnt == max_likes:
            return


def __load_sessions(settings: BotSettings) -> List[BaseSession]:
    session_map = {
        "tinder": TinderSession,
        "okcupid": OkCupidSession,
        "bumble": BumbleSession,
    }
    sessions: List[BaseSession] = []
    for session_name in settings.sessions:
        session_type = session_map.get(session_name.lower())
        if session_type:
            sessions.append(session_type())
    if len(sessions) == 0:
        print("Warning: No sessions specified in settings file")
        sessions = [session_type() for _, session_type in session_map.items()]
    return sessions


def __create_loggers(log_dir: Path = Path("logs")) -> Path:
        """
        Configure root logger: DEBUG -> file, INFO -> console.
        Clears existing handlers to avoid duplicate logs when reloading.
        """
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"log_{timestamp}.txt"

        root_logger = logging.getLogger()
        # remove existing handlers to avoid duplicate entries (useful in REPL / hot-reload)
        if root_logger.handlers:
            root_logger.handlers.clear()

        root_logger.setLevel(logging.DEBUG)

        # file handler (verbose)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        # console handler (concise)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        logging.debug("Initialized logging. Log file: %s", log_file)
        return log_file


def main() -> None:
    # todo- handle no more likes left/no options are left
    settings = __load_bot_settings()
    sessions = __load_sessions(settings)
    log_file = __create_loggers()
    
    while True:
        if not settings.bypass_active_hours and (datetime.now().hour < settings.active_hours_start or datetime.now().hour >= settings.active_hours_end):
            print(f"hour {datetime.now().hour} is not during work hours ({settings.active_hours_start} to {settings.active_hours_end})")
            time.sleep(settings.sleep_time)
            continue
        
        for session in sessions:
            try:
                with session as active_session:
                    if TRY_MESSAGE_BACK:
                        session.enable_ambush()
                        session.get_messaged_matches()
                    __perform_round(active_session, settings)
            except Exception as e:
                print(f"got exception {e}")
                traceback.print_exc()

        print("Sleeping till next session")
        time.sleep(settings.sleep_time)


if __name__ == "__main__":
    main()
