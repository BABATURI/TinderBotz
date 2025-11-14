import os
import random
import time
from pathlib import Path

import undetected_chromedriver as uc
from selenium.common.exceptions import *
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from tinderbotz.helpers.constants_helper import Printouts
from tinderbotz.helpers.geomatch import Geomatch
from tinderbotz.helpers.storage_helper import StorageHelper


class BaseSession:
    def __init__(self, headless=False, store_session=True, user_data=False):
        self.session_data = {
            "duration": 0,
            "like": 0,
            "dislike": 0,
            "superlike": 0
        }
        # self.app_url and self.app_name must be set by children
        self.lower_sleep_time = 1.0
        self.upper_sleep_time = 3.0

        self.start_session = time.time()

        self.started = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        self.headless = headless
        self.store_session = store_session
        self.user_data = user_data

    def __enter__(self) -> 'BaseSession':
        # Go further with the initialisation
        # Setting some options of the browser here below

        options = uc.ChromeOptions()

        # Create empty profile to avoid annoying Mac Popup
        if self.store_session:
            if not self.user_data:
                self.user_data = f"{Path().absolute()}/chrome_profile/"
            if not os.path.isdir(self.user_data):
                os.mkdir(self.user_data)

            Path(f'{self.user_data}First Run').touch()
            options.add_argument(f"--user-data-dir={self.user_data}")

        # options.add_argument("--start-maximized")
        options.add_argument('--no-first-run --no-service-autorun --password-store=basic')
        options.add_argument("--lang=en-GB")

        if self.headless:
            options.headless = True

        # Getting the chromedriver from cache or download it from internet
        print("Getting ChromeDriver ...")
        try:
            self.browser: uc.Chrome = uc.Chrome(options=options)  # ChromeDriverManager().install(),
        except Exception as e:
            print(str(e))
            print("maybe you should update chrome")
            raise e

        # Cool banner
        print(Printouts.BANNER.value)
        time.sleep(1)

        print("Started session: {}\n\n".format(self.started))
        self.browser.get(self.app_url)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        # End session duration
        seconds = int(time.time() - self.start_session)
        self.session_data["duration"] = seconds

        # add session data into a list of messages
        lines = []
        for key in self.session_data:
            message = "{}: {}".format(key, self.session_data[key])
            lines.append(message)

        # print out the statistics of the session
        try:
            BOT_NAME: str = 'BaseBot'
            box = self._get_msg_box(lines=lines, title=BOT_NAME)
            print(box)
        finally:
            print("Started session: {}".format(self.started))
            y = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            print("Ended session: {}".format(y))

        # Close browser properly
        self.browser.quit()

    @property
    def app_url(self) -> str:
        raise NotImplementedError()

    @property
    def does_support_message_on_like(self) -> bool:
        return False

    def set_custom_location(self, latitude, longitude, accuracy="100%"):

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "accuracy": int(accuracy.split('%')[0])
        }

        self.browser.execute_cdp_cmd("Page.setGeolocationOverride", params)

    def _get_home_page(self):
        self.browser.get(self.app_url)
        time.sleep(5)

    # Actions of the session
    def wait_for_login(self):
        if not self._is_logged_in():
            time.sleep(5)
            print('Manual interference is required. Please Login')
            input('press ENTER to continue')

    def _is_logged_in(self):
        raise NotImplementedError()

    def store_local(self, match: Geomatch):
        filename: str = match.match_type
        StorageHelper.store_match(match, directory=os.path.join("data", filename), filename=filename)

    def like(self, randomize_sleep=True, message: Optional[str] = None):
        if message:
            raise NotImplementedError()

        # base option, can be overwritten
        if not self._is_logged_in():
            return
        try:
            action = ActionChains(self.browser)
            action.send_keys(Keys.ARROW_RIGHT).perform()
        except (TimeoutException, ElementClickInterceptedException):
            self._get_home_page()
            return False
        if randomize_sleep:
            time.sleep(random.uniform(self.lower_sleep_time, self.upper_sleep_time))
        return True

    def dislike(self, randomize_sleep=True):
        # base option, can be overwritten
        if not self._is_logged_in():
            return
        try:
            action = ActionChains(self.browser)
            action.send_keys(Keys.ARROW_LEFT).perform()
        except (TimeoutException, ElementClickInterceptedException):
            self._get_home_page()
            return False
        if randomize_sleep:
            time.sleep(random.uniform(self.lower_sleep_time, self.upper_sleep_time))
        return True

    def like_multiple(self, amount=1, ratio='100%', sleep=1, randomize_sleep=True):
        initial_sleep = sleep
        ratio = float(ratio.split('%')[0]) / 100

        if not self._is_logged_in():
            return

        amount_liked = 0
        # handle one time up front, from then on check after every action instead of before
        print("\nLiking profiles started.")
        while amount_liked < amount:
            self._handle_potential_popups()
            # randomize sleep
            if random.random() <= ratio:
                if self.like(randomize_sleep):
                    amount_liked += 1
                    # update for stats after session ended
                    self.session_data['like'] += 1
                    print(f"{amount_liked}/{amount} liked, sleep: {sleep}")
            else:
                self.dislike(randomize_sleep)
                # update for stats after session ended
                self.session_data['dislike'] += 1

        self._print_liked_stats()

    def dislike_multiple(self, amount=1):
        if not self._is_logged_in():
            return

        for _ in range(amount):
            self._handle_potential_popups()
            self.dislike()

            # update for stats after session ended
            self.session_data['dislike'] += 1

        self._print_liked_stats()

    def superlike(self, randomize_sleep=True):
        if not self._is_logged_in():
            return
        try:
            action = ActionChains(self.browser)
            action.send_keys(Keys.ENTER).perform()
        except (TimeoutException, ElementClickInterceptedException):
            self._get_home_page()
            return False
        if randomize_sleep:
            time.sleep(random.uniform(self.lower_sleep_time, self.upper_sleep_time))
        return True

    def get_geomatch(self) -> Geomatch:
        # get current match
        raise NotImplementedError()

    def get_chat_ids(self, new=True, messaged=True):
        raise NotImplementedError()

    def get_new_matches(self, amount=100000):
        raise NotImplementedError()

    def get_messaged_matches(self, amount=100000):
        raise NotImplementedError()

    def send_message(self, chatid, message):
        raise NotImplementedError()

    def send_socials(self, chatid, media):
        # not really hard, just send a fixed msg using
        socials = ""
        self.send_message(chatid, socials)

    def unmatch(self, chatid):
        raise NotImplementedError()

    # Utilities
    def _handle_potential_popups(self):
        raise NotImplementedError()

    def _get_msg_box(self, lines, indent=1, width=None, title=None):
        """Print message-box with optional title."""
        space = " " * indent
        if not width:
            width = max(map(len, lines))
        box = f'/{"=" * (width + indent * 2)}\\\n'  # upper_border
        if title:
            box += f'|{space}{title:<{width}}{space}|\n'  # title
            box += f'|{space}{"-" * len(title):<{width}}{space}|\n'  # underscore
        box += ''.join([f'|{space}{line:<{width}}{space}|\n' for line in lines])
        box += f'\\{"=" * (width + indent * 2)}/'  # lower_border
        return box

    def _print_liked_stats(self):
        likes = self.session_data['like']
        dislikes = self.session_data['dislike']
        superlikes = self.session_data['superlike']

        if superlikes > 0:
            print(
                f"You've superliked {self.session_data['superlike']} profiles during this session.")
        if likes > 0:
            print(f"You've liked {self.session_data['like']} profiles during this session.")
        if dislikes > 0:
            print(f"You've disliked {self.session_data['dislike']} profiles during this session.")
