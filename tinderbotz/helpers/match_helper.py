import time
from typing import Optional

from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from tinderbotz.helpers.constants_helper import Socials
from tinderbotz.helpers.geomatch_svg_mapper import SvgPaths
from tinderbotz.helpers.loadingbar import LoadingBar
from tinderbotz.helpers.match import Match
from tinderbotz.helpers.xpaths import content, modal_manager


class MatchHelper:
	delay = 5

	HOME_URL = "https://tinder.com/app/recs"

	def __init__(self, browser):
		self.browser = browser

	def _scroll_down(self, xpath):
		eula = self.browser.find_element(By.XPATH, xpath)
		self.browser.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', eula)

		SCROLL_PAUSE_TIME = 0.5

		# Get scroll height
		last_height = self.browser.execute_script("arguments[0].scrollHeight", eula)

		while True:
			# Scroll down to bottom
			self.browser.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", eula)

			# Wait to load page
			time.sleep(SCROLL_PAUSE_TIME)

			# Calculate new scroll height and compare with last scroll height
			new_height = self.browser.execute_script("arguments[0].scrollHeight", eula)
			if new_height == last_height:
				return True
			last_height = new_height

	def get_chat_ids(self, new, messaged):
		chatids = []

		xpath = '//button[@role="tab"]'
		try:
			WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located((By.XPATH, xpath)))
		except TimeoutException:
			print("match tab could not be found, trying again")
			self.browser.get(self.HOME_URL)
			time.sleep(1)
			return self.get_chat_ids(new, messaged)

		tabs = self.browser.find_elements(By.XPATH, xpath)

		if new:
			# Make sure we're in the 'new matches' tab
			for tab in tabs:
				if tab.text == 'Matches':
					try:
						tab.click()
					except:
						self.browser.get(self.HOME_URL)
						return self.get_chat_ids(new, messaged)

			# start scraping new matches
			try:
				xpath = '//div[@role="tabpanel"]'

				# wait for element to appear
				WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located((By.XPATH, xpath)))

				div = self.browser.find_element(By.XPATH, xpath)

				list_refs = div.find_elements(By.XPATH, './/div/div/a')
				for index in range(len(list_refs)):
					try:
						ref = list_refs[index].get_attribute('href')
						if "likes-you" in ref or "my-likes" in ref:
							continue
						else:
							chatids.append(ref.split('/')[-1])
					except:
						continue

			except NoSuchElementException:
				pass

		if messaged:
			# Make sure we're in the 'messaged matches' tab
			for tab in tabs:
				if tab.text == 'Messages':
					try:
						tab.click()
					except:
						self.browser.get(self.HOME_URL)
						return self.get_chat_ids(new, messaged)

			# Start scraping the chatted matches
			try:
				xpath = '//div[@class="messageList"]'

				# wait for element to appear
				WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located(
					(By.XPATH, xpath)))

				div = self.browser.find_element(By.XPATH, xpath)

				list_refs = div.find_elements(By.XPATH, './/a')
				for index in range(len(list_refs)):
					try:
						ref = list_refs[index].get_attribute('href')
						chatids.append(ref.split('/')[-1])
					except:
						continue

			except NoSuchElementException:
				pass

		return chatids

	def get_new_matches(self, amount, quickload):
		matches = []
		used_chatids = []
		iteration = 0
		while True:
			iteration += 1
			if len(matches) >= amount:
				break

			new_chatids = self.get_chat_ids(new=True, messaged=False)
			copied = new_chatids.copy()
			for index in range(len(copied)):
				chatid = copied[index]
				if chatid in used_chatids:
					new_chatids.remove(chatid)
				else:
					used_chatids.append(chatid)

			# no new matches are found, MAX LIMIT
			if len(new_chatids) == 0:
				break

			# shorten the list so doesn't fetch ALL matches but just the amount it needs
			diff = len(matches) + len(new_chatids) - amount

			if diff > 0:
				del new_chatids[-diff:]

			print(f"\nGetting not-interacted-with, NEW MATCHES, part {iteration}")
			loadingbar = LoadingBar(len(new_chatids), "new matches")
			for index, chatid in enumerate(new_chatids):
				matches.append(self.get_match(chatid, quickload))
				loadingbar.update_loading(index)
			print("\n")

			# scroll down to get more chatids
			xpath = '//div[@role="tabpanel"]'
			tab = self.browser.find_element(By.XPATH, xpath)
			self.browser.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight;', tab)
			time.sleep(4)

		return matches

	def get_messaged_matches(self, amount, quickload):
		matches = []
		used_chatids = []
		iteration = 0
		while True:
			iteration += 1
			if len(matches) >= amount:
				break

			new_chatids = self.get_chat_ids(new=False, messaged=True)
			copied = new_chatids.copy()
			for index in range(len(copied)):
				if copied[index] in used_chatids:
					new_chatids.remove(copied[index])
				else:
					used_chatids.append(new_chatids[index])

			# no new matches are found, MAX LIMIT
			if len(new_chatids) == 0:
				break

			# shorten the list so doesn't fetch ALL matches but just the amount it needs
			diff = len(matches) + len(new_chatids) - amount
			if diff > 0:
				del new_chatids[-diff:]

			print(f"\nGetting interacted-with, MESSAGED MATCHES, part {iteration}")
			loadingbar = LoadingBar(len(new_chatids), "interacted-with-matches")
			for index, chatid in enumerate(new_chatids):
				matches.append(self.get_match(chatid, quickload))
				loadingbar.update_loading(index)
			print("\n")

			# scroll down to get more chatids
			xpath = '//div[@class="messageList"]'
			tab = self.browser.find_element(By.XPATH, xpath)
			self.browser.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight;', tab)
			time.sleep(4)

		return matches

	def send_message(self, chatid, message):
		if not self._is_chat_opened(chatid):
			self._open_chat(chatid)

		# locate the textbox and send message
		try:
			xpath = '//textarea'

			WebDriverWait(self.browser, self.delay).until(
				EC.presence_of_element_located((By.XPATH, xpath)))

			textbox = self.browser.find_element(By.XPATH, xpath)
			textbox.send_keys(message)
			textbox.send_keys(Keys.ENTER)

			print("Message sent succesfully.\nmessage: {}\n".format(message))

			# sleep so message can be sent
			time.sleep(1.5)
		except Exception as e:
			print("SOMETHING WENT WRONG LOCATING TEXTBOX")
			print(e)

	def send_gif(self, chatid, gifname):
		if not self._is_chat_opened(chatid):
			self._open_chat(chatid)

		try:
			xpath = '/html/body/div[1]/div/div[1]/div/main/div[1]/div/div/div/div[1]/div/div/div[3]/div/div[2]/button'

			WebDriverWait(self.browser, self.delay).until(
				EC.presence_of_element_located((By.XPATH, xpath)))
			gif_btn = self.browser.find_element(By.XPATH, xpath)

			gif_btn.click()
			time.sleep(1.5)

			search_box = self.browser.find_element(By.XPATH, '//textarea')
			search_box.send_keys(gifname)
			# give chance to load gif
			time.sleep(1.5)

			gif = self.browser.find_element(By.XPATH,
			                                '/html/body/div[1]/div/div[1]/div/main/div[1]/div/div/div/div[1]/div/div/div[3]/div/div/div[1]/div[1]/div/div/div')
			gif.click()
			# sleep so gif can be sent
			time.sleep(1.5)

		except Exception as e:
			print(e)

	def send_song(self, chatid, songname):
		if not self._is_chat_opened(chatid):
			self._open_chat(chatid)

		try:
			xpath = '/html/body/div[1]/div/div[1]/div/main/div[1]/div/div/div/div[1]/div/div/div[4]/div/div[3]/button'

			WebDriverWait(self.browser, self.delay).until(
				EC.presence_of_element_located((By.XPATH, xpath)))
			song_btn = self.browser.find_element(By.XPATH, xpath)

			song_btn.click()
			time.sleep(1.5)

			search_box = self.browser.find_element(By.XPATH, '//textarea')
			search_box.send_keys(songname)
			# give chance to load gif
			time.sleep(1.5)

			song = self.browser.find_element(By.XPATH,
			                                 '/html/body/div[1]/div/div[1]/div/main/div[1]/div/div/div/div[1]/div/div/div[3]/div/div[2]/div/div[1]/div[1]/div/div[1]/div/button')
			song.click()
			time.sleep(0.5)

			confirm_btn = self.browser.find_element(By.XPATH,
			                                        '/html/body/div[1]/div/div[1]/div/main/div[1]/div/div/div/div[1]/div/div/div[3]/div/div[2]/div/div[1]/div[2]/div/div[2]/button')
			confirm_btn.click()
			# sleep so song can be sent
			time.sleep(1.5)

		except Exception as e:
			print(e)

	def send_socials(self, chatid, media):
		did_match = False
		for social in (Socials):
			if social == media:
				did_match = True

		if not did_match: print("Media must be of type Socials"); return

		if not self._is_chat_opened(chatid):
			self._open_chat(chatid)

		try:
			xpath = f'{content}/div/div[1]/div/main/div[1]/div/div/div/div[1]/div/div/div[3]/div/div[1]/button'

			WebDriverWait(self.browser, self.delay).until(
				EC.presence_of_element_located((By.XPATH, xpath)))
			socials_btn = self.browser.find_element(By.XPATH, xpath)

			socials_btn.click()
			time.sleep(1)

			xpath = '//img[@alt="{}"]'.format(media.value)
			WebDriverWait(self.browser, self.delay).until(
				EC.presence_of_element_located((By.XPATH, xpath)))
			social_btn = self.browser.find_elements(By.XPATH, xpath)[-1]
			social_btn.click()

			# locate the sendbutton and send social
			try:
				self.browser.find_element(By.XPATH, "//button[@type='submit']").click()
				print("Succesfully send social card")
				# sleep so message can be sent
				time.sleep(1.5)
			except Exception as e:
				print("SOMETHING WENT WRONG LOCATING TEXTBOX")
				print(e)

		except Exception as e:
			print(e)
			self.browser.refresh()
			self.send_socials(chatid, media)

	def unmatch(self, chatid):
		if not self._is_chat_opened(chatid):
			self._open_chat(chatid)

		try:
			# '//button[text()="Unmatch"]'
			unmatch_button = self.browser.find_element(By.XPATH,
			                                           f'{content}/div/div[1]/div/main/div[1]/div/div/div/div[2]/div/div[2]/div/button[1]')
			unmatch_button.click()
			time.sleep(1)

			unmatch_button = self.browser.find_element(By.XPATH, f'{modal_manager}/div/div/div[2]/button[1]')
			unmatch_button.click()
			time.sleep(1)

		except Exception as e:
			print("SOMETHING WENT WRONG FINDING THE UNMATCH BUTTONS")
			print(e)

	def _open_chat(self, chatid):
		if self._is_chat_opened(chatid): return;

		href = "/app/messages/{}".format(chatid)

		# look for the match with that chatid
		# first we're gonna look for the match in the already interacted matches
		try:
			xpath = '//*[@role="tab"]'
			# wait for element to appear
			WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located((By.XPATH, xpath)))

			tabs = self.browser.find_elements(By.XPATH, xpath)
			for tab in tabs:
				if tab.text == "Messages":
					tab.click()
			time.sleep(1)
		except Exception as e:
			self.browser.get(self.HOME_URL)
			print(e)
			return self._open_chat(chatid)

		try:
			match_button = self.browser.find_element(By.XPATH, '//a[@href="{}"]'.format(href))
			self.browser.execute_script("arguments[0].click();", match_button)

		except Exception as e:
			# match reference not found, so let's see if match exists in the new not yet interacted matches
			xpath = '//*[@role="tab"]'
			# wait for element to appear
			WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located((By.XPATH, xpath)))

			tabs = self.browser.find_elements(By.XPATH, xpath)
			for tab in tabs:
				if tab.text == "Matches":
					tab.click()

			time.sleep(1)

			try:
				matched_button = self.browser.find_element(By.XPATH, '//a[@href="{}"]'.format(href))
				matched_button.click()
			except Exception as e:
				# some kind of error happened, probably cuz chatid/ref/match doesnt exist (anymore)
				# Another error could be that the elements could not be found, cuz we're at a wrong url (potential bug)
				print(e)
		time.sleep(1)

	def get_match(self, chatid: str):
		if not self._is_chat_opened(chatid):
			self._open_chat(chatid)

		name: Optional[str] = self.get_name(chatid)
		age: Optional[str] = self.get_age(chatid)
		bio: Optional[str] = self.get_bio(chatid)
		passions: Optional[str] = self.get_passions(chatid)
		match: Match = Match(name=name, chatid=chatid, age=age, bio=bio, passions=passions)

		self.__complete_match(match, chatid)

		return match

	def get_name(self, chatid):
		if not self._is_chat_opened(chatid):
			self._open_chat(chatid)

		try:
			xpath = f'{content}/div/div[1]/div/main/div[1]/div/div/div/div[2]/div/div[1]/div/div/div[2]/div[1]/div/div[1]/div[1]/h1'
			element = self.browser.find_element(By.XPATH, xpath)
			WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located((By.XPATH, xpath)))
			return element.text
		except Exception as e:
			print(e)

	def get_age(self, chatid):
		if not self._is_chat_opened(chatid):
			self._open_chat(chatid)

		age = None

		try:
			xpath = f'{content}/div/div[1]/div/main/div[1]/div/div/div/div[2]/div/div[1]/div/div/div[2]/div[1]/div/div[1]/span'
			element = self.browser.find_element(By.XPATH, xpath)
			WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located(
				(By.XPATH, xpath)))
			try:
				age = int(element.text)
			except ValueError:
				age = None
		except:
			pass

		return age

	def __complete_match(self, match: Match, chatid: str) -> None:
		if not self._is_chat_opened(chatid):
			self._open_chat(chatid)

		xpath = '//div[@class="Row"]'
		rows = self.browser.find_elements(By.XPATH, xpath)

		for row in rows:
			svg = row.find_element(By.XPATH, ".//*[starts-with(@d, 'M')]").get_attribute('d')
			value = row.find_element(By.XPATH, ".//div[2]").text
			if svg == SvgPaths.WORK_SVG_PATH:
				match.work = value
			if svg == SvgPaths.STUDYING_SVG_PATH:
				match.study = value
			if svg == SvgPaths.HOME_SVG_PATH:
				match.home = value.split(' ')[-1]
			if svg == SvgPaths.GENDER_SVG_PATH:
				match.gender = value
			if svg == SvgPaths.LOCATION_SVG_PATH or svg == SvgPaths.LOCATION_SVG_PATH2:
				distance = value.split(' ')[0]
				try:
					distance = int(distance)
				except TypeError:
					# Means the text has a value of 'Less than 1 km away'
					distance = 1
				except ValueError:
					distance = None

				match.distance = distance

	def get_passions(self, chatid: str) -> str:
		if not self._is_chat_opened(chatid):
			self._open_chat(chatid)

		passions = []
		xpath = f'{content}/div/div[1]/div/main/div[1]/div/div/div/div[2]/div/div[1]/div/div/div[2]/div/div/div[2]/div[2]/div'
		elements = self.browser.find_elements(By.XPATH, xpath)
		for el in elements:
			passions.append(el.text)

		return ', '.join(passions)

	def get_bio(self, chatid: str):
		if not self._is_chat_opened(chatid):
			self._open_chat(chatid)

		try:
			xpath = f'{content}/div/div[1]/div/main/div[1]/div/div/div/div[2]/div/div[1]/div/div/div[2]/div[2]/div'
			return self.browser.find_element(By.XPATH, xpath).text
		except:
			# no bio included?
			return None

	def _is_chat_opened(self, chatid: str):
		# open the correct user if not happened yet
		if chatid in self.browser.current_url:
			return True
		else:
			return False
