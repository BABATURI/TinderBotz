import json
import logging
import time
from typing import List, Optional

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

    def superlike(self, randomize_sleep=True):
        superlike_btn = self.browser.find_element(By.XPATH,
                                                  "//div[@class='encounters-action tooltip-activator encounters-action--superswipe']")
        superlike_btn.click()
        if randomize_sleep:
            time.sleep(self.lower_sleep_time)

    def _handle_potential_popups(self):
        # TODO: fill in here
        return

    def _parse_about_badges_bio(self, story_content: WebElement, geomatch: Geomatch) -> bool:
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
            lis = story_content.find_elements(By.TAG_NAME, "li")
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
                bio = story_content.find_element(By.XPATH, bio_xpath).text
                if geomatch.bio:
                    geomatch.bio += "\n" + bio
                else:
                    geomatch.bio = bio
            except:
                pass
            return True
        except:
            return False

    def _parse_picture(self, story_content: WebElement, geomatch: Geomatch) -> bool:
        xpath = ".//img[@class='media-box__picture-image']"
        try:
            # should be only one img
            for img in story_content.find_elements(By.XPATH, xpath):
                url = img.get_attribute('src')
                # url = url.split("&wm_size=")[0]
                geomatch.image_urls.append(url)
                return True
            return False
        except:
            return False

    def _parse_name_age_work(self, story_content, geomatch: Geomatch) -> bool:
        name_xpath = ".//span[@class='encounters-story-profile__name']"
        age_xpath = ".//span[@class='encounters-story-profile__age']"
        work_xpath = ".//div[@class='encounters-story-profile__details']"
        try:
            # should be only one img
            name: str = story_content.find_element(By.XPATH, name_xpath).text
            age: str = story_content.find_element(By.XPATH, age_xpath).text
            work: List[WebElement] = story_content.find_elements(By.XPATH, work_xpath)

            if "," in age:
                age = age.split(", ")[1]
            geomatch.name = name
            geomatch.age = age
            if len(work) > 0:
                geomatch.work = work[0].text.split('\n')[0]
            return True
        except:
            return False

    def _parse_prompts(self, story_content: WebElement, geomatch: Geomatch) -> bool:
        q_xpath = ".//div[@class='encounters-story-section__heading-title']"
        a_xpath = ".//div[@class='encounters-story-section__content']"
        prompts = []
        try:
            # should be only one prompt
            story_content.find_element(By.XPATH,
                                       ".//section[@class='encounters-story-section encounters-story-section--question']")
            pname: str = story_content.find_element(By.XPATH, q_xpath).find_element(By.TAG_NAME, "h2").get_attribute(
                "innerHTML")
            value: str = story_content.find_element(By.XPATH, a_xpath).find_element(By.TAG_NAME, "p").get_attribute(
                "innerHTML")

            prompts.append((pname, value))
            # TODO: add to geomatch
            return True
        except:
            return False

    def _parse_location(self, story_content: WebElement, geomatch: Geomatch) -> bool:
        xpath = "//div[@class='location-widget__pill']"
        try:
            story_content.find_element(By.XPATH,
                                       ".//section[@class='encounters-story-section encounters-story-section--location']")
            location_str = story_content.find_element(By.XPATH, xpath).text
            # TODO: validate output
            geomatch.home = location_str
            return True
        except:
            return False

    def get_geomatch(self, quickload: bool = True) -> Optional[Geomatch]:
        if not self._is_logged_in():
            return None

        xpath = "//div[@class='encounters-action tooltip-activator encounters-action--superswipe']"
        WebDriverWait(self.browser, 5).until(
            EC.presence_of_element_located((By.XPATH, xpath)))

        geomatch = Geomatch()
        album_article_xpath = "//div[@class='encounters-story__content']"
        for story_content in self.browser.find_elements(By.XPATH, album_article_xpath):
            # try to parse as picture
            logger.debug("content -> %s", str(story_content))
            if self._parse_picture(story_content, geomatch):
                continue
            # try to parse as profile name / age
            if self._parse_name_age_work(story_content, geomatch):
                continue
            # try to parse as about badges
            if self._parse_about_badges_bio(story_content, geomatch):
                continue
            # try to parse as prompt
            if self._parse_prompts(story_content, geomatch):
                continue

            if self._parse_location(story_content, geomatch):
                continue

        # BUG: an image can already be in the same as list...
        # if len(geomatch.image_urls) > 1:
        #     geomatch.image_urls.pop()
        geomatch.gen_id()
        return geomatch

    def get_chat_ids(self, new: bool = True, messaged: bool = True) -> Optional[List[str]]:
        # todo implement
        raise NotImplementedError()

    def get_new_matches(self, amount: int = 100000, quickload: bool = True) -> Optional[List[Geomatch]]:
        # todo implement
        raise NotImplementedError()

    def get_messaged_matches(self, amount: int = 100000, quickload: bool = True) -> Optional[List[Geomatch]]:
        # todo implement
        raise NotImplementedError()

    def send_message(self, chatid: str, message: str) -> None:
        # todo implement
        raise NotImplementedError()

    def unmatch(self, chatid: str) -> None:
        # todo implement
        raise NotImplementedError()
