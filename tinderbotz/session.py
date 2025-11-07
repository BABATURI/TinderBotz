# Selenium: automation of browser
# from webdriver_manager.chrome import ChromeDriverManager
# some other imports :-)
import time

from selenium.common.exceptions import NoSuchElementException, TimeoutException, \
	ElementNotVisibleException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from basebot.basebot import BaseSession
from basebot.match import Geomatch
from tinderbotz.helpers.email_helper import EmailHelper
# Tinderbotz: helper classes
from tinderbotz.helpers.geomatch import Geomatch
from tinderbotz.helpers.geomatch_helper import GeomatchHelper
from tinderbotz.helpers.match_helper import MatchHelper
from tinderbotz.helpers.preferences_helper import PreferencesHelper
from tinderbotz.helpers.profile_helper import ProfileHelper
from tinderbotz.helpers.xpaths import *


class Session(BaseSession):
	HOME_URL = "https://www.tinder.com/app/recs"
	app_name = "tinder"
	app_url = "https://tinder.com/app/recs"
	app_logged_in_match = "tinder.com/app"

	def __init__(self, headless=False, store_session=True, proxy=None, user_data=False):
		self.email = None
		self.may_send_email = False
		self.session_data = {
			"duration": 0,
			"like": 0,
			"dislike": 0,
			"superlike": 0
		}

		super().__init__(headless, store_session, user_data)

	# This will send notification when you get a match to your email used to logged in.
	def set_email_notifications(self, boolean):
		self.may_send_email = boolean

	def set_distance_range(self, km):
		assert self._is_logged_in()

		helper = PreferencesHelper(browser=self.browser)
		helper.set_distance_range(km)

	def set_age_range(self, min, max):
		assert self._is_logged_in()

		helper = PreferencesHelper(browser=self.browser)
		helper.set_age_range(min, max)

	def set_sexuality(self, type):
		assert self._is_logged_in()

		helper = PreferencesHelper(browser=self.browser)
		helper.set_sexualitiy(type)

	def set_global(self, boolean):
		assert self._is_logged_in()

		helper = PreferencesHelper(browser=self.browser)
		helper.set_global(boolean)

	def set_bio(self, bio):
		helper = ProfileHelper(browser=self.browser)
		helper.set_bio(bio)

	def add_photo(self, filepath):
		helper = ProfileHelper(browser=self.browser)
		helper.add_photo(filepath)

	def _is_logged_in(self):
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

	def get_geomatch(self, quickload=True):
		if not self._is_logged_in():
			return

		helper = GeomatchHelper(browser=self.browser)
		self._handle_potential_popups()
		# TODO: refactor this entire mess of GeomatchHelper
		name = helper.get_name()
		age = helper.get_age()

		bio, _, _, _, anthem, looking_for = helper.get_bio_and_passions()
		images = helper.get_images()
		instagram = helper.get_insta(bio)
		rowdata = {'interests': []}
		work = rowdata.get('work')
		study = rowdata.get('education')
		home = rowdata.get('home')
		distance = rowdata.get('distance')
		gender = rowdata.get('gender')
		passions = " ".join(rowdata['interests'])
		lifestyle = f"smoking: {rowdata.get('smoking')}\ndrinking: {rowdata.get('drinking')}\nworkout: {rowdata.get('workout')}"
		basics = f"zodiac: {rowdata.get('zodiac')}"

		return Geomatch(name=name, age=age, work=work, gender=gender, study=study, home=home,
		                distance=distance,
		                bio=bio, passions=passions, lifestyle=lifestyle, basics=basics,
		                anthem=anthem, looking_for=looking_for, instagram=instagram, images=images)

	def get_chat_ids(self, new=True, messaged=True):
		if self._is_logged_in():
			helper = MatchHelper(browser=self.browser)
			self._handle_potential_popups()
			return helper.get_chat_ids(new, messaged)

	def get_new_matches(self, amount=100000, quickload=True):
		if self._is_logged_in():
			helper = MatchHelper(browser=self.browser)
			self._handle_potential_popups()
			return helper.get_new_matches(amount, quickload)

	def get_messaged_matches(self, amount=100000, quickload=True):
		if self._is_logged_in():
			helper = MatchHelper(browser=self.browser)
			self._handle_potential_popups()
			return helper.get_messaged_matches(amount, quickload)

	def send_message(self, chatid, message):
		if self._is_logged_in():
			helper = MatchHelper(browser=self.browser)
			self._handle_potential_popups()
			helper.send_message(chatid, message)

	def send_gif(self, chatid, gifname):
		if self._is_logged_in():
			helper = MatchHelper(browser=self.browser)
			self._handle_potential_popups()
			helper.send_gif(chatid, gifname)

	def send_song(self, chatid, songname):
		if self._is_logged_in():
			helper = MatchHelper(browser=self.browser)
			self._handle_potential_popups()
			helper.send_song(chatid, songname)

	def send_socials(self, chatid, media):
		if self._is_logged_in():
			helper = MatchHelper(browser=self.browser)
			self._handle_potential_popups()
			helper.send_socials(chatid, media)

	def unmatch(self, chatid):
		if self._is_logged_in():
			helper = MatchHelper(browser=self.browser)
			self._handle_potential_popups()
			helper.unmatch(chatid)

	# Utilities
	def _handle_potential_popups(self):
		delay = 0.25

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
		matched = False
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

# def _is_logged_in(self):
#     # make sure tinder website is loaded for the first time
#     if not "tinder" in self.browser.current_url:
#         # enforce english language
#         self.browser.get("https://tinder.com/?lang=en")
#         time.sleep(1.5)

#     if "tinder.com/app/" in self.browser.current_url:
#         return True
#     else:
#         print("User is not logged in yet.\n")
#         return False
