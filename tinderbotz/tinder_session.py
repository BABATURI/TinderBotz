import time
from typing import Optional, List

from selenium.common.exceptions import NoSuchElementException, TimeoutException, \
    ElementNotVisibleException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from tinderbotz.base_session import BaseSession
from tinderbotz.helpers.email_helper import EmailHelper
from tinderbotz.helpers.geomatch import Geomatch
from tinderbotz.helpers.geomatch_helper import GeomatchHelper
from tinderbotz.helpers.match_helper import MatchHelper
from tinderbotz.helpers.preferences_helper import PreferencesHelper
from tinderbotz.helpers.profile_helper import ProfileHelper
from tinderbotz.helpers.xpaths import *


class TinderSession(BaseSession):
    HOME_URL: str = "https://www.tinder.com/app/recs"
    app_name: str = "tinder"
    app_logged_in_match: str = "tinder.com/app"

    def __init__(self, headless: bool = False, store_session: bool = True, user_data: bool = False) -> None:
        self.email: Optional[str] = None
        self.may_send_email: bool = False
        self.session_data: dict[str, int] = {
            "duration": 0,
            "like": 0,
            "dislike": 0,
            "superlike": 0
        }

        super().__init__(headless, store_session, user_data)

    @property
    def app_url(self) -> str:
        return "https://tinder.com/app/recs"

    # This will send notification when you get a match to your email used to logged in.
    def set_email_notifications(self, boolean: bool) -> None:
        self.may_send_email = boolean

    def set_distance_range(self, km: int) -> None:
        assert self._is_logged_in()

        helper = PreferencesHelper(browser=self.browser)
        helper.set_distance_range(km)

    def set_age_range(self, min: int, max: int) -> None:
        assert self._is_logged_in()

        helper = PreferencesHelper(browser=self.browser)
        helper.set_age_range(min, max)

    def set_sexuality(self, type: str) -> None:
        assert self._is_logged_in()

        helper = PreferencesHelper(browser=self.browser)
        helper.set_sexualitiy(type)

    def set_global(self, boolean: bool) -> None:
        assert self._is_logged_in()

        helper = PreferencesHelper(browser=self.browser)
        helper.set_global(boolean)

    def set_bio(self, bio: str) -> None:
        helper = ProfileHelper(browser=self.browser)
        helper.set_bio(bio)

    def add_photo(self, filepath: str) -> None:
        helper = ProfileHelper(browser=self.browser)
        helper.add_photo(filepath)

    def _is_logged_in(self) -> bool:
        # make sure tinder website is loaded for the first time
        if not self.app_logged_in_match in self.browser.current_url:
            # enforce english language
            self.browser.get(self.app_url)
            time.sleep(5)

        if self.app_logged_in_match in self.browser.current_url:
            return True
        else:
            print("User is not logged in yet.\n")
            return False

    def get_geomatch(self) -> Optional[Geomatch]:
        if not self._is_logged_in():
            return None

        helper: GeomatchHelper = GeomatchHelper(browser=self.browser)
        self._handle_potential_popups()

        return helper.get_geomatch()

    def get_chat_ids(self, new: bool = True, messaged: bool = True) -> Optional[List[str]]:
        if self._is_logged_in():
            helper: MatchHelper = MatchHelper(browser=self.browser)
            self._handle_potential_popups()
            return helper.get_chat_ids(new, messaged)
        return None

    def get_new_matches(self, amount: int = 100000) -> Optional[List[Geomatch]]:
        if self._is_logged_in():
            helper: MatchHelper = MatchHelper(browser=self.browser)
            self._handle_potential_popups()
            return helper.get_new_matches(amount)
        return None

    def get_messaged_matches(self, amount: int = 100000) -> Optional[List[Geomatch]]:
        if self._is_logged_in():
            helper: MatchHelper = MatchHelper(browser=self.browser)
            self._handle_potential_popups()
            return helper.get_messaged_matches(amount)
        return None

    def send_message(self, chatid: str, message: str) -> None:
        if self._is_logged_in():
            helper: MatchHelper = MatchHelper(browser=self.browser)
            self._handle_potential_popups()
            helper.send_message(chatid, message)

    def send_gif(self, chatid: str, gifname: str) -> None:
        if self._is_logged_in():
            helper: MatchHelper = MatchHelper(browser=self.browser)
            self._handle_potential_popups()
            helper.send_gif(chatid, gifname)

    def send_song(self, chatid: str, songname: str) -> None:
        if self._is_logged_in():
            helper: MatchHelper = MatchHelper(browser=self.browser)
            self._handle_potential_popups()
            helper.send_song(chatid, songname)

    def send_socials(self, chatid: str, media: str) -> None:
        if self._is_logged_in():
            helper: MatchHelper = MatchHelper(browser=self.browser)
            self._handle_potential_popups()
            helper.send_socials(chatid, media)

    def unmatch(self, chatid: str) -> None:
        if self._is_logged_in():
            helper: MatchHelper = MatchHelper(browser=self.browser)
            self._handle_potential_popups()
            helper.unmatch(chatid)

    # Utilities
    def _handle_potential_popups(self) -> Optional[str]:
        delay: float = 0.25

        # last possible id based div
        base_element = self.browser.find_element(By.XPATH, modal_manager)

        # try to deny see who liked you
        try:
            xpath = './/main/div/div/div[3]/button[2]'
            WebDriverWait(base_element, delay).until(
                EC.presence_of_element_located((By.XPATH, xpath)))

            deny_btn = base_element.find_element(By.XPATH, xpath)
            deny_btn.click()
            return "POPUP: Denied see who liked you"

        except NoSuchElementException:
            pass
        except TimeoutException:
            pass

        # Try to dismiss a potential 'upgrade like' popup
        try:
            # locate "no thanks"-button
            xpath = './/main/div/button[2]'
            base_element.find_element(By.XPATH, xpath).click()
            return "POPUP: Denied upgrade to superlike"
        except NoSuchElementException:
            pass

        # try to deny 'add tinder to homescreen'
        try:
            xpath = './/main/div/div[2]/button[2]'

            add_to_home_popup = base_element.find_element(By.XPATH, xpath)
            add_to_home_popup.click()
            return "POPUP: Denied Tinder to homescreen"

        except NoSuchElementException:
            pass

        # deny buying more superlikes
        try:
            xpath = './/main/div/div[3]/button[2]'
            deny = base_element.find_element(By.XPATH, xpath)
            deny.click()
            return "POPUP: Denied buying more superlikes"
        except NoSuchElementException:
            pass

        # try to dismiss match
        matched: bool = False
        try:
            xpath = '//button[@title="Back to Tinder"]'

            match_popup = base_element.find_element(By.XPATH, xpath)
            match_popup.click()
            matched = True

        except NoSuchElementException:
            pass
        except:
            matched = True
            self.browser.refresh()

        if matched and self.may_send_email:
            try:
                EmailHelper.send_mail_match_found(self.email)
            except:
                print("Some error occurred when trying to send mail.")
                print("Consider opening an Issue on Github.")
                pass
            return "POPUP: Dismissed NEW MATCH"

        # try to say 'no thanks' to buy more (super)likes
        try:
            xpath = './/main/div/div[3]/button[2]'
            deny_btn = base_element.find_element(By.XPATH, xpath)
            deny_btn.click()
            return "POPUP: Denied buying more superlikes"

        except ElementNotVisibleException:
            # element is not clickable, probably cuz it's out of view but still there
            self.browser.refresh()
        except NoSuchElementException:
            pass
        except:
            # TBD add stale element exception for now just refresh page
            self.browser.refresh()
            pass

        # Deny confirmation of email
        try:
            xpath = './/main/div/div[1]/div[2]/button[2]'
            remindmelater = base_element.find_element(By.XPATH, xpath)
            remindmelater.click()

            time.sleep(3)
            # handle other potential popups
            self._handle_potential_popups()
            return "POPUP: Deny confirmation of email"
        except:
            pass

        # Deny add location popup
        try:
            xpath = ".//*[contains(text(), 'No Thanks')]"
            nothanks = base_element.find_element(By.XPATH, xpath)
            nothanks.click()
            time.sleep(3)
            # handle other potential popups
            self._handle_potential_popups()
            return "POPUP: Deny confirmation of email"
        except:
            pass

        return None
