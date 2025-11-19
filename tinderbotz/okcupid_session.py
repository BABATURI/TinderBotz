import logging
import random
import time
from typing import List, Optional, Tuple, Dict

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from undetected_chromedriver import WebElement

from tinderbotz.base_session import BaseSession
from tinderbotz.helpers.geomatch import Geomatch

logger = logging.getLogger(__file__)


class OkCupidSession(BaseSession):
    app_name: str = "okcupid"
    app_logged_in_match: str = "okcupid.com/discover"

    def __init__(self, headless=False, store_session=True, user_data=False):
        super().__init__(headless, store_session, user_data)

    @property
    def app_url(self):
        return "https://www.okcupid.com/discover"

    @property
    def does_support_message_on_like(self) -> bool:
        return True

    def _is_logged_in(self) -> bool:
        # make sure cupid website is loaded for the first time
        if self.app_logged_in_match not in self.browser.current_url:
            self.browser.get(self.app_url)
            time.sleep(10)
            print(f'slept 5 secs')

        try:
            xpath = '//*[@id="stack-menu-item-JUST_FOR_YOU"]/span'
            WebDriverWait(self.browser, 5).until(
                EC.presence_of_element_located((By.XPATH, xpath)))
            return True
        except:
            print("User is not logged in okcupid yet.\n")

            return False

    def dislike(self, randomize_sleep=True):
        dislike_btn = self.browser.find_element(By.XPATH,
                                                "//button[@class='dt-action-buttons-button pass']")
        dislike_btn.click()
        if randomize_sleep:
            time.sleep(random.uniform(self.lower_sleep_time, self.upper_sleep_time))
        self.session_data['dislike'] += 1
        return True

    def like(self, randomize_sleep=True, message: Optional[str] = None):
        if not message:
            like_btn = self.browser.find_element(By.XPATH,
                                                 "//button[@class='dt-action-buttons-button like']")
            like_btn.click()
            if randomize_sleep:
                time.sleep(random.uniform(self.lower_sleep_time, self.upper_sleep_time))
        else:
            FIRST_IMAGE_INTRO_XPATH: str = '//*[@id="quickmatch-aria-tabpanel"]/div/div/div[1]/div[2]/div/div[2]/div/div[1]/button'
            self.browser.find_element(By.XPATH, FIRST_IMAGE_INTRO_XPATH).click()
            time.sleep(0.5)
            INTRO_MESSAGE_BOX_XPATH: str = '//*[@id="messenger-composer"]'
            # TODO: fix crash here sometimes, DO NOT SEND EMOJIS!!!
            self.browser.find_element(By.XPATH, INTRO_MESSAGE_BOX_XPATH).send_keys(message)
            
            SEND_MESSAGE_XPATH: str = '//*[@id="OkModal"]/div[1]/div/div/div/div[3]/button'
            self.browser.find_element(By.XPATH, SEND_MESSAGE_XPATH).click()

            WAIT_FOR_BOX_TO_DISAPPEAR: int = 1
            time.sleep(WAIT_FOR_BOX_TO_DISAPPEAR)

        self._handle_potential_popups()
        if randomize_sleep:
            self._random_sleep()
        self.session_data['like'] += 1
        return True

    def superlike(self, randomize_sleep=True):
        superlike_btn = self.browser.find_element(By.XPATH,
                                                  "//div[@class='superlike-button-object']")
        superlike_btn.click()
        if randomize_sleep:
            time.sleep(random.uniform(self.lower_sleep_time, self.upper_sleep_time))
        self.session_data['superlike'] += 1
        return True

    def _handle_potential_popups(self):
        LIKE_THEM_ANYWAY_XPATH: str = '//*[@id="BaseModal"]/button[2]'

        elements: List[WebElement] = self.browser.find_elements(By.XPATH, LIKE_THEM_ANYWAY_XPATH)

        for element in elements:
            if element.text == 'LIKE THEM ANYWAY':
                element.click()
                return

    def __get_user_id(self) -> str:
        # todo- fix no such method
        div = self.browser.find_element(By.XPATH, "//div[@class='desktop-dt-wrapper']")
        user_id = div.get_attribute("data-user-id")
        return user_id

    def get_geomatch(self) -> Geomatch:
        assert self._is_logged_in()

        name_xpath = "//h2[@class='card-content-header__text']"
        WebDriverWait(self.browser, 5).until(
            EC.presence_of_element_located((By.XPATH, name_xpath)))
        # name, age
        name = self.browser.find_element(By.XPATH, name_xpath).text
        age_location = self.browser.find_element(By.XPATH, "//div[@class='card-content-header__location']").text
        if " • " in age_location:
            age, location = age_location.split(" • ")[:2]
        else:
            age = age_location
            location = ""
        
        try:
            age = int(age.strip())
        except ValueError:
            age = age_location.strip()
        # get bio
        bio = ""
        for a in self.browser.find_elements(By.XPATH, "//span[@class='dt-essay-text']"):
            bio = a.text
        # get pics
        urls = []
        first_photo_div = self.browser.find_element(By.XPATH, "//div[@class='dt-photo dt-photo-superlikes']")
        # todo- handle selenium.common.exceptions.ElementNotInteractableException
        try:
            first_photo_div.click()
        except Exception as e:
            print(f"got exception {e}, retrying")
            time.sleep(2)

            first_photo_div.click()
        #     wait for img elements to load
        time.sleep(1)
        for img in self.browser.find_elements(By.XPATH,
                                              "//img[@class='fade-in-transition-300 fade-in-transition-ease fade-in-transition-appear-done fade-in-transition-enter-done']"):
            img_url = img.get_attribute("src")
            urls.append(img_url)
            time.sleep(0.25)
        #     close pics
        action = ActionChains(self.browser)
        action.send_keys(Keys.ESCAPE).perform()
        time.sleep(0.5)
        # get row data
        # basics, background, lifestyle, looking_for, ...
        rowdata = {}
        for div in self.browser.find_elements(By.XPATH, "//div[contains(@class, 'matchprofile-details-section')]"):
            div_class = div.get_attribute("class")
            category = div_class.split("matchprofile-details-section--")[1]
            if category == "wiw":
                category = "looking_for"

            rowdata[category] = div.text  # maybe get child divs text

        # TODO: promtps - press a button to expand prompts? parse them them go back a page
        m = Geomatch(
            name=name, age=age, home=location,
            image_urls=urls,
            basics=rowdata.get("basics", ""),
            lifestyle=rowdata.get("lifestyle", ""),
            looking_for=rowdata.get("looking_for", ""),
            passions=rowdata.get("passions", ""),
            bio=bio,
            prompts=self.__get_prompts()
        )
        m.id = self.__get_user_id()
        return m

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

    def __get_prompts(self) -> Dict[str, str]:
        prompts: Dict[str, str] = {}

        idx: int = 1
        while True:
            PROMPT_QUESTION_XPATH: str = f'//*[@id="quickmatch-aria-tabpanel"]/div/div/div[2]/div[{idx}]/h3'
            question_elements: List[WebElement] = self.browser.find_elements(By.XPATH, PROMPT_QUESTION_XPATH)

            PROMPT_ANSWER_XPATH: str = f'//*[@id="quickmatch-aria-tabpanel"]/div/div/div[2]/div[{idx}]/div/div/span'
            answer_elements: List[WebElement] = self.browser.find_elements(By.XPATH, PROMPT_ANSWER_XPATH)

            if len(question_elements) == 0 or len(answer_elements) == 0:
                break

            prompts[question_elements[0].text] = answer_elements[0].text

            idx += 1

        return prompts
