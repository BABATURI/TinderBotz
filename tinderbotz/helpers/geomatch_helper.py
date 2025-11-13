import re
import time
import logging
from typing import Optional, Dict, Any, List

import undetected_chromedriver as uc
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from tinderbotz.helpers.geomatch import Geomatch
from tinderbotz.helpers.geomatch_svg_mapper import SvgPaths
from tinderbotz.helpers.xpaths import content


logger = logging.getLogger(__file__)


class GeomatchHelper:
    DELAY: int = 5
    HOME_URL: str = "https://www.tinder.com/app/recs"
    browser: uc.Chrome

    def __init__(self, browser: uc.Chrome) -> None:
        self.browser: uc.Chrome = browser
        if "/app/recs" not in self.browser.current_url:
            self._get_home_page()

        # TODO: sync geomatch state
        try:
            WebDriverWait(self.browser, 20.0).until(EC.presence_of_element_located(
                (By.XPATH, "//div[@class='Bdrs(8px) Bgz(cv) Bgp(c) StretchedBox']")))
        except Exception:
            raise

    def like(self) -> bool:
        try:
            action: ActionChains = ActionChains(self.browser)
            action.send_keys(Keys.ARROW_RIGHT).perform()
            return True

        except (TimeoutException, ElementClickInterceptedException):
            self._get_home_page()

        return False

    def dislike(self) -> None:
        try:
            action: ActionChains = ActionChains(self.browser)
            action.send_keys(Keys.ARROW_LEFT).perform()

        # time.sleep(1)
        except (TimeoutException, ElementClickInterceptedException):
            self._get_home_page()

    def superlike(self) -> None:
        try:
            if 'profile' in self.browser.current_url:
                xpath: str = f'{content}/div/div[1]/div/main/div[1]/div/div/div[1]/div[2]/div/div/div[3]/div/div/div/button'

                # wait for element to appear
                WebDriverWait(self.browser, self.DELAY).until(EC.presence_of_element_located(
                    (By.XPATH, xpath)))

                superlike_button: WebElement = self.browser.find_element(By.XPATH, xpath)

                superlike_button.click()

            else:
                xpath: str = f'{content}/div/div[1]/div/main/div[1]/div/div/div[1]'

                WebDriverWait(self.browser, self.DELAY).until(EC.presence_of_element_located(
                    (By.XPATH, xpath)))

                card: WebElement = self.browser.find_element(By.XPATH, xpath)

                action: ActionChains = ActionChains(self.browser)
                action.drag_and_drop_by_offset(card, 0, -200).perform()

            time.sleep(1)

        except (TimeoutException, ElementClickInterceptedException):
            self._get_home_page()

    def get_geomatch(self) -> Optional[Geomatch]:
        self._open_profile()

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

    def _close_profile(self) -> None:
        action: ActionChains = ActionChains(self.browser)
        action.send_keys(Keys.ARROW_DOWN).perform()

    def _open_profile(self, second_try: bool = False) -> None:
        try:
            action: ActionChains = ActionChains(self.browser)
            action.send_keys(Keys.ARROW_UP).perform()

        # time.sleep(1)

        except (ElementClickInterceptedException, TimeoutException):
            if not second_try:
                print("Trying again to locate the profile info button in a few seconds")
                time.sleep(2)
                self._open_profile(second_try=True)
            else:
                self.browser.refresh()
        except Exception:
            self.browser.get(self.HOME_URL)
            if not second_try:
                self._open_profile(second_try=True)

    def __get_name(self) -> Optional[str]:
        self._open_profile()

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
        self._open_profile()

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

    def is_verified(self) -> bool:
        self._open_profile()
        found: bool = False
        xpath_badge: str = f'{content}/div/div[1]/div/main/div[1]/div/div/div[1]/div[1]/div/div[2]/div[1]/div/div[1]/div[2]'
        try:
            self.browser.find_element(By.XPATH, xpath_badge)
            found = True
        except Exception:
            pass
        return found

    def __complete_geomatch(self, geomatch: Geomatch) -> None:
        rowdata: Dict[str, Any] = {
            "interests": []
        }
        # return rowdata
        self._open_profile()
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
                SvgPaths.HEIGHT_SVG: "height",
                SvgPaths.DISTANCE_SVG: "distance",
                SvgPaths.WORK_SVG_PATH: "work",
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
        self._open_profile()

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

    @staticmethod
    def de_emojify(text: str) -> str:
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
            ig: str = self.de_emojify(description[x])
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

    def _get_home_page(self) -> None:
        self.browser.get(self.HOME_URL)
        time.sleep(10)

    @staticmethod
    def __extract_image_url(image_outer_html: str) -> str:
        URL_INDICATOR: str = 'https'
        url_start: int = image_outer_html.find(URL_INDICATOR)

        html_from_after_url_beginning: str = image_outer_html[url_start:]
        URL_END_IDX: int = html_from_after_url_beginning.find("&quot;)")

        return html_from_after_url_beginning[:URL_END_IDX].replace("&amp;", "&")
