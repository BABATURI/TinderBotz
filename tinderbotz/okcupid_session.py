import json
import random
import logging
import time
from typing import List, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

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

    def _is_logged_in(self) -> bool:
        # make sure tinder website is loaded for the first time
        if not self.app_logged_in_match in self.browser.current_url:
            self.browser.get(self.app_url)
            time.sleep(5)

        if self.app_logged_in_match in self.browser.current_url:
            return True
        else:
            print("User is not logged in yet.\n")
            return False

    def dislike(self, randomize_sleep=True):
        dislike_btn = self.browser.find_element(By.XPATH,
                                                  "//button[@class='dt-action-buttons-button pass']")
        dislike_btn.click()
        if randomize_sleep:
            time.sleep(random.uniform(self.lower_sleep_time, self.upper_sleep_time))
            
    def like(self, randomize_sleep=True):
        like_btn = self.browser.find_element(By.XPATH,
                                                  "//button[@class='dt-action-buttons-button like']")
        like_btn.click()
        if randomize_sleep:
            time.sleep(random.uniform(self.lower_sleep_time, self.upper_sleep_time))
    
    def superlike(self, randomize_sleep=True):
        superlike_btn = self.browser.find_element(By.XPATH,
                                                  "//div[@class='superlike-button-object']")
        superlike_btn.click()
        if randomize_sleep:
            time.sleep(random.uniform(self.lower_sleep_time, self.upper_sleep_time))

    def _handle_potential_popups(self):
        # TODO: fill in here
        return
    
    def _get_user_id(self) -> str:
        div = self.browser.find_element(By.XPATH, "//div[@class='desktop-dt-wrapper']")
        user_id = div.get_attribute("data-user-id") 
        return user_id
    
    def _format_row_data(self, raw_text: str) -> List[str]:
        return [p for p in raw_text.split(' | ') if p]
    
    def get_geomatch(self, quickload: bool = True) -> Optional[Geomatch]:
        if not self._is_logged_in():
            return None
        
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
        age = int(age.strip())
        # get bio
        bio = ""
        for a in self.browser.find_elements(By.XPATH, "//span[@class='dt-essay-text']"):
            bio = a.text
        # get pics
        urls = []
        first_photo_div = self.browser.find_element(By.XPATH, "//div[@class='dt-photo dt-photo-superlikes']")
        first_photo_div.click_safe()
        #     wait for img elements to load
        time.sleep(1)
        for img in self.browser.find_elements(By.XPATH, "//img[@class='fade-in-transition-300 fade-in-transition-ease fade-in-transition-appear-done fade-in-transition-enter-done']"):
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
        )
        m.id = self._get_user_id()
        return m

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
