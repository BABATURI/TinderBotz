import json
import logging
import time
import traceback
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from dating_llm.agent import *
from tinderbotz.base_session import BaseSession
from tinderbotz.bumble_session import BumbleSession
from tinderbotz.helpers.bot_settings import BotSettings
from tinderbotz.helpers.storage_helper import StorageHelper
from tinderbotz.okcupid_session import OkCupidSession
from tinderbotz.tinder_session import Geomatch, TinderSession


def _create_dating_agent() -> DatingLLM:
    config_file: Path = Path("configuration", "user_pref")

    user_pref: str = "I like fit and slim, blonde / hazel haired women with bright eyes who enjoy outdoor activities and have a good sense of humor."
    if config_file.exists():
        with open(config_file, "r") as f:
            user_pref = f.read()
    else:
        print("Creating default user preference file...")
        with open(config_file, "w") as f:
            f.write(user_pref)

    return DatingLLM(user_pref)


def _load_bot_settings() -> BotSettings:
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


def _create_loggers(log_dir: Path = Path("logs")) -> Path:
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
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter("%(asctime)s:%(name)s:%(levelname)s:%(message)s")
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


# TODO: refactor this to be not ugly
class Main:
    def __init__(self):
        self._dating_agent = _create_dating_agent()
        self._log_file = _create_loggers()
        self._settings = _load_bot_settings()
        self._sessions = self._load_sessions_by_config()


    def get_response_from_dating_agent(self, geomatch: Geomatch) -> Dict[str, Any]:
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
        image_urls: List[str] = geomatch.image_urls[:6]

        ai_json_response, total_tokens = self._dating_agent.run_llm(query, image_urls)
        logging.info(f"Total tokens used: {total_tokens}")
        return ai_json_response


    def _perform_round(self, active_session: BaseSession) -> None:
        settings: BotSettings = self._settings
        max_likes = settings.max_likes_per_session
        max_swipes = settings.max_swipes_per_session

        location: Tuple[float, float] = settings.location
        active_session.set_custom_location(latitude=location[0], longitude=location[1])

        active_session.wait_for_login()

        likes_cnt: int = 0

        for _ in range(max_swipes):
            geomatch: Geomatch = active_session.get_geomatch()

            logging.info("running dating LLM query...")
            decision_json: Dict[str, Any] = self.get_response_from_dating_agent(geomatch)

            logging.info(f"Decision for {geomatch.name}, age {geomatch.age}:\n{decision_json}")
            if decision_json.get("decision", "") not in ("like", "dislike"):
                active_session.browser.refresh()
                time.sleep(5)
                continue

            is_liked: bool = decision_json["decision"]

            GEOMATCHES_STORAGE_DIR: str = os.path.join(Path(os.path.abspath(__file__)).parent, "data")
            StorageHelper.store_match(geomatch, GEOMATCHES_STORAGE_DIR, is_liked)

            if not is_liked:
                active_session.dislike()
                continue

            active_session.like(
                message=decision_json.get("like_message", "") if active_session.does_support_message_on_like else None)
            likes_cnt += 1

            if likes_cnt == max_likes:
                return
    
    def perform_all_rounds(self) -> None:
        for session in self._sessions:
            try:
                with session as active_session:
                    self._perform_round(active_session)
            except Exception as e:
                logging.error(f"got exception {e}:")
                logging.error("%s", traceback.format_exc())

    def _load_sessions_by_config(self) -> List[BaseSession]:
        settings: BotSettings = self._settings
        # TODO: refactor to get all subclasses of BaseSession automatically
        session_map = {
            "tinder": TinderSession,
            "okcupid": OkCupidSession,
            "bumble": BumbleSession,
        }
        sessions: List[BaseSession] = []

        for session_name in settings.sessions:
            session_class = session_map.get(session_name.lower())
            if session_class:
                sessions.append(session_class())
        if sessions == []:
            logging.warning("No sessions specified in settings file")
            sessions = [TinderSession(), OkCupidSession(), BumbleSession()]
        return sessions

    def get_sleep_time(self) -> int:
        return self._settings.sleep_time
    
    def is_in_active_hours(self) -> bool:
        current_hour: int = datetime.now().hour
        return (self._settings.active_hours_start <= current_hour < self._settings.active_hours_end) or self._settings.bypass_active_hours
    
    def close(self) -> None:
        self._dating_agent.close()





def main() -> None:
    # todo- handle no more likes left/no options are left
    main_app = Main()
    settings: BotSettings = main_app._settings
    
    while True:
        if not main_app.is_in_active_hours():
            logging.info(f"hour {datetime.now().hour} is not during work hours ({settings.active_hours_start} to {settings.active_hours_end})")
            time.sleep(main_app.get_sleep_time())
            continue
        
        main_app.perform_all_rounds()
        
        logging.info("Sleeping till next session")
        time.sleep(main_app.get_sleep_time())


if __name__ == "__main__":
    main()
