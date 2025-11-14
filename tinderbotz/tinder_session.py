import logging
import re
import time
from typing import Optional, Dict, Any, List

from selenium.common.exceptions import NoSuchElementException, ElementNotVisibleException
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from tinderbotz.base_session import BaseSession
from tinderbotz.helpers.email_helper import EmailHelper
from tinderbotz.helpers.geomatch import Geomatch
from tinderbotz.helpers.tinder_svg_mapper import TinderSvgPaths
from tinderbotz.helpers.tinder_match_helper import TinderMatchHelper
from tinderbotz.helpers.preferences_helper import PreferencesHelper
from tinderbotz.helpers.profile_helper import ProfileHelper
from tinderbotz.helpers.xpaths import *

logger = logging.getLogger(__file__)


class TinderSession(BaseSession):
    HOME_URL: str = "https://www.tinder.com/app/recs"
    app_name: str = "tinder"
    app_logged_in_match: str = "tinder.com/app"
    DELAY: int = 5

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

        if "/app/recs" not in self.browser.current_url:
            self.browser.get(self.HOME_URL)
            time.sleep(10)

        WebDriverWait(self.browser, 20.0).until(EC.presence_of_element_located(
            (By.XPATH, "//div[@class='Bdrs(8px) Bgz(cv) Bgp(c) StretchedBox']")))

        self._handle_potential_popups()

        return self.__get_geomatch()

    def get_chat_ids(self, new: bool = True, messaged: bool = True) -> Optional[List[str]]:
        if self._is_logged_in():
            helper: TinderMatchHelper = TinderMatchHelper(browser=self.browser)
            self._handle_potential_popups()
            return helper.get_chat_ids(new, messaged)
        return None

    def get_new_matches(self, amount: int = 100000) -> Optional[List[Geomatch]]:
        if self._is_logged_in():
            helper: TinderMatchHelper = TinderMatchHelper(browser=self.browser)
            self._handle_potential_popups()
            return helper.get_new_matches(amount)
        return None

    def get_messaged_matches(self, amount: int = 100000) -> Optional[List[Geomatch]]:
        if self._is_logged_in():
            helper: TinderMatchHelper = TinderMatchHelper(browser=self.browser)
            self._handle_potential_popups()
            return helper.get_messaged_matches(amount)
        return None

    def send_message(self, chatid: str, message: str) -> None:
        if self._is_logged_in():
            helper: TinderMatchHelper = TinderMatchHelper(browser=self.browser)
            self._handle_potential_popups()
            helper.send_message(chatid, message)

    def send_gif(self, chatid: str, gifname: str) -> None:
        if self._is_logged_in():
            helper: TinderMatchHelper = TinderMatchHelper(browser=self.browser)
            self._handle_potential_popups()
            helper.send_gif(chatid, gifname)

    def send_song(self, chatid: str, songname: str) -> None:
        if self._is_logged_in():
            helper: TinderMatchHelper = TinderMatchHelper(browser=self.browser)
            self._handle_potential_popups()
            helper.send_song(chatid, songname)

    def send_socials(self, chatid: str, media: str) -> None:
        if self._is_logged_in():
            helper: TinderMatchHelper = TinderMatchHelper(browser=self.browser)
            self._handle_potential_popups()
            helper.send_socials(chatid, media)

    def unmatch(self, chatid: str) -> None:
        if self._is_logged_in():
            helper: TinderMatchHelper = TinderMatchHelper(browser=self.browser)
            self._handle_potential_popups()
            helper.unmatch(chatid)

    def __get_geomatch(self) -> Optional[Geomatch]:
        self.__open_profile()

        name: Optional[str] = self.__get_name()
        age: Optional[int] = self.__get_age()
        bio: Optional[str] = self.__get_bio()
        looking_for: Optional[str] = self.__get_looking_for()
        image_urls: List[str] = self.__get_image_urls()
        instagram: Optional[str] = self.__get_insta(bio)

        geomatch: Geomatch = Geomatch(
            name=name,
            age=age,
            looking_for=looking_for,
            instagram=instagram,
            image_urls=image_urls)

        self.__complete_geomatch(geomatch)

        return geomatch

    def __open_profile(self, second_try: bool = False) -> None:
        try:
            action: ActionChains = ActionChains(self.browser)
            action.send_keys(Keys.ARROW_UP).perform()

        # time.sleep(1)

        except (ElementClickInterceptedException, TimeoutException):
            if not second_try:
                print("Trying again to locate the profile info button in a few seconds")
                time.sleep(2)
                self.__open_profile(second_try=True)
            else:
                self.browser.refresh()
        except Exception:
            self.browser.get(self.HOME_URL)
            if not second_try:
                self.__open_profile(second_try=True)

    def __get_name(self) -> Optional[str]:
        self.__open_profile()

        try:
            NAME_XPATH: str = '//*[@id="main-content"]/div[1]/div/div/div/div[1]/div[1]/div[1]/div/div/h1/span[1]'

            # wait for element to appear
            WebDriverWait(self.browser, self.DELAY).until(EC.presence_of_element_located(
                (By.XPATH, NAME_XPATH)))

            element: WebElement = self.browser.find_element(By.XPATH, NAME_XPATH)

            return element.text
        except Exception:
            return None

    def __get_age(self) -> Optional[int]:
        self.__open_profile()

        age: Optional[int] = None

        try:
            xpath: str = f'//*[@id="main-content"]/div[1]/div/div/div/div[1]/div[1]/div[1]/div/div/h1/span[2]'

            # wait for element to appear
            WebDriverWait(self.browser, self.DELAY).until(EC.presence_of_element_located(
                (By.XPATH, xpath)))

            element: WebElement = self.browser.find_element(By.XPATH, xpath)
            try:
                age = int(element.text)
            except ValueError:
                age = None
        except Exception:
            pass

        return age

    def __complete_geomatch(self, geomatch: Geomatch) -> None:
        rowdata: Dict[str, Any] = {
            "interests": []
        }
        # return rowdata
        self.__open_profile()
        # iterate this content to find items

        list_items: List[WebElement] = self.browser.find_elements(By.TAG_NAME, "li")
        for li in list_items:
            if li.text == '':
                continue
            # check for messages
            if len(li.find_elements(By.TAG_NAME, 'a')) > 0:
                continue
            logger.debug(li.text)
            # special case for interests:
            try:
                interest: WebElement = li.find_element(By.XPATH, ".//div/span")
                rowdata["interests"].append(interest.text)
                continue
            except Exception:
                pass
            # special case for q&a
            try:
                q: str = li.find_element(By.TAG_NAME, "h3").text.lower()
                if q == "How often do you smoke?".lower():
                    q = "smoking"
                a: str = li.find_element(By.XPATH, ".//div/div/div[2]").text
                rowdata[q] = a
                continue
            except Exception:
                pass
            # else, essentials
            svg: List[WebElement] = li.find_elements(By.TAG_NAME, "svg")
            if len(svg) != 1:
                continue
            svg_val: Optional[str] = svg[0].get_attribute('outerHTML')
            elements: List[WebElement] = li.find_elements(By.XPATH, ".//div/div/div")

            if not elements:
                continue

            value: str = elements[0].text

            # Note: we can extend this for more info
            SVG_MAP: Dict[str, str] = {
                TinderSvgPaths.HEIGHT_SVG: "height",
                TinderSvgPaths.DISTANCE_SVG: "distance",
                TinderSvgPaths.WORK_SVG_PATH: "work",
            }

            if SVG_MAP.get(svg_val) is not None:
                category: Optional[str] = SVG_MAP.get(svg_val)
                if category is not None:
                    rowdata[category] = value

                    if category == "distance":
                        distance: str = value.replace("kilometres away", "km")
                        rowdata['distance'] = distance

        geomatch.work = rowdata.get('work')
        geomatch.study = rowdata.get('education')
        geomatch.home = rowdata.get('home')
        geomatch.distance = rowdata.get('distance')
        geomatch.gender = rowdata.get('gender')
        geomatch.passions = ", ".join(rowdata['interests'])
        geomatch.lifestyle = f"smoking: {rowdata.get('smoking')}\ndrinking: {rowdata.get('drinking')}\nworkout: {rowdata.get('workout')}"
        geomatch.basics = f"zodiac: {rowdata.get('zodiac')}"

    def __get_bio(self) -> Optional[str]:
        try:
            return self.browser.find_element(By.XPATH,
                                             "//div[@class='C($c-ds-text-primary) Typs(body-1-regular)']").text
        except:
            return None

    def __get_looking_for(self) -> Optional[str]:
        try:
            xpath: str = "//span[@class='Typs(display-3-strong) C($c-ds-text-primary) Mstart(4px)']"
            return self.browser.find_element(By.XPATH, xpath).text

        except:
            return None

    def __get_image_urls(self) -> List[str]:
        self.__open_profile()

        images: List[str] = []
        idx: int = 0
        while True:
            elements: List[WebElement] = self.browser.find_elements(By.XPATH,
                                                                    f'//*[@id="carousel-item-{idx}"]/div/div')

            idx += 1

            if len(elements) == 0:
                break

            outer_html: Optional[str] = elements[0].get_attribute("outerHTML")
            if not outer_html:
                continue

            images.append(self.__extract_image_url(outer_html))
            # print(images)
            action: ActionChains = ActionChains(self.browser)
            action.send_keys(Keys.SPACE).perform()
            time.sleep(0.33)

        return images

    def __get_insta(self, text: Optional[str]) -> Optional[str]:
        """Take the bio and read line by line to match if the description
        contain an instagram user.
        Args:
            text (string): string with emojis or not
        Returns:
            ig (string): return valid instagram user.
        """
        if not text:
            return None
        valid_pattern: List[str] = [
            "@",
            "ig-",
            "ig",
            "ig:",
            "ing",
            "ing:",
            "instag",
            "instag:",
            "insta:",
            "insta",
            "inst",
            "inst:",
            "instagram",
            "instagram:",
        ]
        description: List[str] = text.rstrip().lower().strip().split()
        for x in range(len(description)):
            ig: str = self.__de_emojify(description[x])
            if '@' in ig:
                return ig.replace('@', '')
            elif ig in valid_pattern:
                try:
                    if ':' in description[x + 1]:
                        return description[x + 2]
                    else:
                        return description[x + 1]
                except Exception:
                    return None
            else:
                try:
                    ig_parts: List[str] = ig.split(':', 1)
                    if ig_parts[0] in valid_pattern:
                        return ig_parts[-1]
                except Exception:
                    return None
        return None

    @staticmethod
    def __extract_image_url(image_outer_html: str) -> str:
        URL_INDICATOR: str = 'https'
        url_start: int = image_outer_html.find(URL_INDICATOR)

        html_from_after_url_beginning: str = image_outer_html[url_start:]
        URL_END_IDX: int = html_from_after_url_beginning.find("&quot;)")

        return html_from_after_url_beginning[:URL_END_IDX].replace("&amp;", "&")

    @staticmethod
    def __de_emojify(text: str) -> str:
        """Remove emojis from a string
        Args:
            text (string): string with emojis or not
        Returns:
            string: recompile string without emojis
        """
        regrex_pattern = re.compile(
            pattern="["
                    u"\U0001F600-\U0001F64F"  # emoticons
                    u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                    u"\U0001F680-\U0001F6FF"  # transport & map symbols
                    u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                    "]+",
            flags=re.UNICODE,
        )
        return regrex_pattern.sub(r'', text)

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
