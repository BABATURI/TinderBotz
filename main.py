import json
import time
import traceback
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from dating_llm.gemini_dating_llm import *
from dating_llm.openrouter_dating_llm import OpenRouterDatingLLM
from tinderbotz.base_session import BaseSession
from tinderbotz.bumble_session import BumbleSession
from tinderbotz.helpers.bot_settings import BotSettings
from tinderbotz.helpers.storage_helper import StorageHelper
from tinderbotz.okcupid_session import OkCupidSession
from tinderbotz.tinder_session import Geomatch, TinderSession

TRY_MESSAGE_BACK = True
TRUST_BUT_VERIFY = False


def __get_user_pref() -> str:
    user_pref: Path = Path("configuration", "user_pref.txt")
    if not user_pref.exists():
        raise Exception(f"Create user pref file at {user_pref}")

    with open(user_pref, "r") as f:
        return f.read()


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


def __get_response_from_dating_agent(settings: BotSettings, geomatch: Geomatch) -> DecisionResponse:
    # Note: to save tokens we don't save everything - only what matters
    _looks = geomatch.looks if "cm" in geomatch.looks else None
    minimized_duplicate_geomatch: Geomatch = Geomatch(name=geomatch.name,
                                                      age=geomatch.age,
                                                      work=geomatch.work,
                                                      study=geomatch.study,
                                                      bio=geomatch.bio,
                                                      basics=geomatch.basics,
                                                      lifestyle=geomatch.lifestyle,
                                                      passions=geomatch.passions,
                                                      looks=geomatch.looks,
                                                      looking_for=geomatch.looking_for,
                                                      prompts=geomatch.prompts)

    query: str = (f"Full profile info:\n"
                  f"{json.dumps({x: y for x, y in asdict(minimized_duplicate_geomatch).items() if y not in (None, '', [])}, indent=4)}")
    
    assert settings.image_count_to_use > 1, "You must let the bot see an image, or else whats the point?"

    image_urls: List[str] = geomatch.image_urls[:settings.image_count_to_use - 1]
    if len(geomatch.image_urls) > 0:
        image_urls.append(geomatch.image_urls[-1])

    user_pref: str = __get_user_pref()
    main_model = OpenRouterDatingLLM(user_pref)
    verify_model = GeminiDatingLLM(user_pref)
    if not TRUST_BUT_VERIFY:
        main_model = OpenRouterDatingLLM(user_pref)
    
    ai_json_response, total_tokens = main_model.run_llm(query, image_urls)
    print(f"Total tokens used by Open Router: {total_tokens}")

    if not ai_json_response.is_like:
        return ai_json_response

    if not TRUST_BUT_VERIFY:
        return ai_json_response
    
    print("Making sure with gemini")

    gemini_ai_json_response, gemini_total_tokens = verify_model.run_llm(query, image_urls)
    print(f"Total tokens used by Gemini: {gemini_total_tokens}")
    
    # patch like message, because openrouter is shitty
    ai_json_response.like_message = gemini_ai_json_response.like_message
    return ai_json_response if gemini_ai_json_response.is_like else gemini_ai_json_response


def __perform_round(active_session: BaseSession, settings: BotSettings) -> None:
    max_likes = settings.max_likes_per_session
    max_swipes = settings.max_swipes_per_session

    location: Tuple[float, float] = settings.location
    active_session.set_custom_location(latitude=location[0], longitude=location[1])

    likes_cnt: int = 0

    active_session.wait_for_login()
    for _ in range(max_swipes):
        try:
            geomatch: Geomatch = active_session.get_geomatch()

            print("running dating LLM query...")
            decision: DecisionResponse = __get_response_from_dating_agent(settings, geomatch)

            print(f"Decision for {geomatch.name}, age {geomatch.age}:\n{decision}")

            GEOMATCHES_STORAGE_DIR: str = os.path.join(Path(os.path.abspath(__file__)).parent, "data")
            StorageHelper.store_match(geomatch, GEOMATCHES_STORAGE_DIR, decision)

            if decision.is_like:
                active_session.like(
                    message=decision.like_message if active_session.does_support_message_on_like else None)
                likes_cnt += 1
            else:
                active_session.dislike()
            
            time.sleep(3)
            if likes_cnt == max_likes:
                return
        except Exception as e:
            print(f'got exeption: {e}')
            traceback.print_exc()
            active_session.browser.refresh()
            time.sleep(5)


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
    __create_loggers()

    while True:
        if not settings.bypass_active_hours and (
                datetime.now().hour < settings.active_hours_start or datetime.now().hour >= settings.active_hours_end):
            print(
                f"hour {datetime.now().hour} is not during work hours ({settings.active_hours_start} to {settings.active_hours_end})")
            time.sleep(settings.sleep_time)
            continue

        for session in sessions:
            try:
                with session as active_session:
                    if settings.allow_ambush:
                        session.enable_ambush()  # todo- fix only for cupid here
                        session.get_messaged_matches()
                    __perform_round(active_session, settings)
            except Exception as e:
                print(f"got exception: {e}")
                traceback.print_exc()

        print("Sleeping till next session")
        time.sleep(settings.sleep_time)


if __name__ == "__main__":
    main()
