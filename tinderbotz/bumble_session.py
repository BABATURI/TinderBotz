import json
import logging
import time
from typing import List, Optional, Dict

from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from tinderbotz.base_session import BaseSession
from tinderbotz.helpers.geomatch import Geomatch

logger = logging.getLogger(__file__)


class BumbleSession(BaseSession):
    app_name: str = "bumble"
    app_logged_in_match: str = "bumble.com/app"

    def __init__(self, headless=False, store_session=True, user_data=False):
        super().__init__(headless, store_session, user_data)

    @property
    def app_url(self):
        return "https://bumble.com/app"

    def _is_logged_in(self) -> bool:
        # make sure bumble website is loaded for the first time
        if not self.app_logged_in_match in self.browser.current_url:
            # enforce english language
            self.browser.get(self.app_url)
            time.sleep(5)

        if self.app_logged_in_match in self.browser.current_url:
            return True
        else:
            print("User is not logged in yet.\n")
            return False

    def superlike(self, randomize_sleep=True):
        superlike_btn = self.browser.find_element(By.XPATH,
                                                  "//div[@class='encounters-action tooltip-activator encounters-action--superswipe']")
        superlike_btn.click()
        if randomize_sleep:
            time.sleep(self.lower_sleep_time)

    def _handle_potential_popups(self):
        # TODO: fill in here
        return

    def __complete_about_badges_bio(self, geomatch: Geomatch) -> bool:
        IMG_TO_BADGE_MAP = {
            "https://fr1.ecdn2.bumbcdn.com/i/big/assets/bumble_lifestyle_badges/normal/web/standard/sz___size__/ic_badge_profileChips_dating_heightv2.png": "height",
            "https://fr1.ecdn2.bumbcdn.com/i/big/assets/bumble_lifestyle_badges/normal/web/standard/sz___size__/ic_badge_profileChips_dating_drinkingv2.png": "drinking",
            "https://fr1.ecdn2.bumbcdn.com/i/big/assets/bumble_lifestyle_badges/normal/web/standard/sz___size__/ic_badge_profileChips_dating_smokingv2.png": "smoking",
            "https://fr1.ecdn2.bumbcdn.com/i/big/assets/bumble_lifestyle_badges/normal/web/standard/sz___size__/ic_badge_profileChips_dating_intentionsv2.png": "looking for",
            "https://fr1.ecdn2.bumbcdn.com/i/big/assets/bumble_lifestyle_badges/normal/web/standard/sz___size__/ic_badge_profileChips_dating_familyPlansv2.png": "children",
            "https://fr1.ecdn2.bumbcdn.com/i/big/assets/bumble_lifestyle_badges/normal/web/standard/sz___size__/ic_badge_profileChips_dating_exercisev2.png": "workout",
            "https://fr1.ecdn2.bumbcdn.com/i/big/assets/bumble_lifestyle_badges/normal/web/standard/sz___size__/ic_badge_profileChips_dating_educationv2.png": "education",
        }
        # try to parse bio, its also here apparently
        bio_xpath = ".//p[@class='encounters-story-about__text']"
        # trigger only once...
        if geomatch.lifestyle:
            return False
        extra_info = {}
        try:
            lis = self.browser.find_elements(By.TAG_NAME, "li")
            if lis == []:
                return False
            for li in lis:
                tag_image = li.find_element(By.TAG_NAME, "img")
                img_src = tag_image.get_attribute("src")
                value = tag_image.get_attribute("alt")
                if IMG_TO_BADGE_MAP.get(img_src):
                    cat = IMG_TO_BADGE_MAP.get(img_src)
                    extra_info[cat] = value
            # TODO: un-fuckup this
            if extra_info.get("looking for"):
                geomatch.looking_for = extra_info.get("looking for")
                extra_info.pop("looking for")
            if extra_info.get("education"):
                geomatch.study = extra_info.get("education")
                extra_info.pop("education")
            geomatch.lifestyle = json.dumps(extra_info)

            try:
                ActionChains(self.browser).send_keys(Keys.ARROW_DOWN).perform()
                time.sleep(0.5)

                bio = self.browser.find_element(By.XPATH, bio_xpath).text
                if geomatch.bio:
                    geomatch.bio += "\n" + bio
                else:
                    geomatch.bio = bio
            except:
                pass
            return True
        except:
            return False

    def __complete_image_urls(self, geomatch: Geomatch) -> None:
        album_article_xpath = "//div[@class='encounters-story__content']"
        for story_content in self.browser.find_elements(By.XPATH, album_article_xpath):
            xpath = ".//img[@class='media-box__picture-image']"
            for img in story_content.find_elements(By.XPATH, xpath):
                url = img.get_attribute('src')
                geomatch.image_urls.append(url)

    def __complete_name_age_work(self, geomatch: Geomatch) -> bool:
        name_xpath = ".//span[@class='encounters-story-profile__name']"
        age_xpath = ".//span[@class='encounters-story-profile__age']"
        work_xpath = ".//div[@class='encounters-story-profile__details']"
        try:
            # should be only one img
            name: str = self.browser.find_element(By.XPATH, name_xpath).text
            age: str = self.browser.find_element(By.XPATH, age_xpath).text
            work: List[WebElement] = self.browser.find_elements(By.XPATH, work_xpath)

            if "," in age:
                age = age.split(", ")[1]
            geomatch.name = name
            geomatch.age = age
            if len(work) > 0:
                geomatch.work = work[0].text.split('\n')[0]
            return True
        except:
            return False

    def __complete_prompts(self, geomatch: Geomatch) -> None:
        ActionChains(self.browser).send_keys(Keys.ARROW_DOWN).perform()
        time.sleep(0.5)

        idx: int = 3

        miss_counter: int = 0
        prompts: Dict[str, str] = {}
        while miss_counter < 6:
            answer_xpath = f'//*[@id="main"]/div/div[1]/main/div[2]/div/div/span/div[1]/article/div[1]/div[{idx}]/article/div[2]/section/div/p'
            question_xpath = f'//*[@id="main"]/div/div[1]/main/div[2]/div/div/span/div[1]/article/div[1]/div[{idx}]/article/div[2]/section/header/div[2]/h2'
            answer_matches: List[WebElement] = self.browser.find_elements(By.XPATH, answer_xpath)
            question_matches: List[WebElement] = self.browser.find_elements(By.XPATH, question_xpath)

            if not answer_matches or not question_matches or not answer_matches[0] or not question_matches[0]:
                miss_counter += 1
            else:
                prompts[question_matches[0].text] = answer_matches[0].text

            idx += 1

            ActionChains(self.browser).send_keys(Keys.ARROW_DOWN).perform()
            time.sleep(0.5)

        geomatch.prompts = prompts

    def __complete_location(self, geomatch: Geomatch) -> None:
        try:
            xpath = "//div[@class='location-widget__pill']"
            location_str = self.browser.find_element(By.XPATH, xpath).text
            geomatch.home = location_str
        except:
            pass

    def get_geomatch(self) -> Geomatch:
        assert self._is_logged_in()

        xpath = "//div[@class='encounters-action tooltip-activator encounters-action--superswipe']"
        WebDriverWait(self.browser, 5).until(
            EC.presence_of_element_located((By.XPATH, xpath)))

        geomatch = Geomatch()
        self.__complete_name_age_work(geomatch)
        self.__complete_image_urls(geomatch)
        self.__complete_about_badges_bio(geomatch)
        self.__complete_prompts(geomatch)
        self.__complete_location(geomatch)

        # BUG: an image can already be in the same as list...
        # if len(geomatch.image_urls) > 1:
        #     geomatch.image_urls.pop()
        geomatch.gen_id()
        return geomatch

    def get_chat_ids(self, new: bool = True, messaged: bool = True) -> Optional[List[str]]:
        # todo implement
        raise NotImplementedError()

    def get_new_matches(self, amount: int = 100000) -> Optional[List[Geomatch]]:
        # todo implement
        raise NotImplementedError()

    def get_messaged_matches(self, amount: int = 100000) -> Optional[List[Geomatch]]:
        # todo implement
        raise NotImplementedError()

    def send_message(self, chatid: str, message: str) -> None:
        # todo implement
        raise NotImplementedError()

    def unmatch(self, chatid: str) -> None:
        # todo implement
        raise NotImplementedError()
