from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import *
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import re
from tinderbotz.helpers.xpaths import content
from datetime import datetime


class GeomatchHelper:
	DELAY = 5
	HOME_URL = "https://www.tinder.com/app/recs"
	NAME_XPATH = '//*[@id="main-content"]/div[1]/div/div/div/div[1]/div[1]/div[1]/div/div/h1/span[1]'

	def __init__(self, browser):
		self.browser = browser
		self.opened_profile = False
		if "/app/recs" not in self.browser.current_url:
			self._get_home_page()
   
		# TODO: sync geomatch state
		try:
			WebDriverWait(self.browser, 20.0).until(EC.presence_of_element_located(
					(By.XPATH, "//div[@class='Bdrs(8px) Bgz(cv) Bgp(c) StretchedBox']")))
		except:
			pass

	def like(self) -> bool:
		try:
			action = ActionChains(self.browser)
			action.send_keys(Keys.ARROW_RIGHT).perform()
			return True

		except (TimeoutException, ElementClickInterceptedException):
			self._get_home_page()

		return False

	def dislike(self):
		try:
			action = ActionChains(self.browser)
			action.send_keys(Keys.ARROW_LEFT).perform()

		# time.sleep(1)
		except (TimeoutException, ElementClickInterceptedException):
			self._get_home_page()

	def superlike(self):
		try:
			if 'profile' in self.browser.current_url:
				xpath = f'{content}/div/div[1]/div/main/div[1]/div/div/div[1]/div[2]/div/div/div[3]/div/div/div/button'

				# wait for element to appear
				WebDriverWait(self.browser, self.DELAY).until(EC.presence_of_element_located(
					(By.XPATH, xpath)))

				superlike_button = self.browser.find_element(By.XPATH, xpath)

				superlike_button.click()

			else:
				xpath = f'{content}/div/div[1]/div/main/div[1]/div/div/div[1]'

				WebDriverWait(self.browser, self.DELAY).until(EC.presence_of_element_located(
					(By.XPATH, xpath)))

				card = self.browser.find_element(By.XPATH, xpath)

				action = ActionChains(self.browser)
				action.drag_and_drop_by_offset(card, 0, -200).perform()

			time.sleep(1)

		except (TimeoutException, ElementClickInterceptedException):
			self._get_home_page()
   
	def _close_profile(self, second_try=False):
		action = ActionChains(self.browser)
		action.send_keys(Keys.ARROW_DOWN).perform()
		self.opened_profile = False
   
	def _open_profile(self, second_try=False):
		try:
			action = ActionChains(self.browser)
			action.send_keys(Keys.ARROW_UP).perform()
			self.opened_profile = True

		# time.sleep(1)

		except (ElementClickInterceptedException, TimeoutException):
			if not second_try:
				print("Trying again to locate the profile info button in a few seconds")
				time.sleep(2)
				self._open_profile(second_try=True)
			else:
				self.browser.refresh()
		except:
			self.browser.get(self.HOME_URL)
			if not second_try:
				self._open_profile(second_try=True)

	def get_name(self):
		self._open_profile()

		try:
			xpath = '//*[@id="main-content"]/div[1]/div/div/div/div[1]/div[1]/div[1]/div/div/h1/span[1]'
			# wait for element to appear
			WebDriverWait(self.browser, self.DELAY).until(EC.presence_of_element_located(
				(By.XPATH, self.NAME_XPATH)))

			element = self.browser.find_element(By.XPATH, self.NAME_XPATH)
			
			return element.text
		except Exception as e:
			return None

	def get_age(self):
		self._open_profile()

		age = None

		try:
			xpath = f'//*[@id="main-content"]/div[1]/div/div/div/div[1]/div[1]/div[1]/div/div/h1/span[2]'

			# wait for element to appear
			WebDriverWait(self.browser, self.DELAY).until(EC.presence_of_element_located(
				(By.XPATH, xpath)))

			element = self.browser.find_element(By.XPATH, xpath)
			try:
				age = int(element.text)
			except ValueError:
				age = None
		except:
			pass

		
		return age

	def is_verified(self):
		self._open_profile()
		found = False
		xpath_badge = f'{content}/div/div[1]/div/main/div[1]/div/div/div[1]/div[1]/div/div[2]/div[1]/div/div[1]/div[2]'
		try:
			self.browser.find_element(By.XPATH, xpath_badge)
			found = True
		except:
			pass
		return found

	_WORK_SVG = "M7.15 3.434h5.7V1.452a.728.728 0 0 0-.724-.732H7.874a.737.737 0 0 0-.725.732v1.982z"
	_STUDYING_SVG_PATH = "M11.87 5.026L2.186 9.242c-.25.116-.25.589 0 .705l.474.204v2.622a.78.78 0 0 0-.344.657c0 .42.313.767.69.767.378 0 .692-.348.692-.767a.78.78 0 0 0-.345-.657v-2.322l2.097.921a.42.42 0 0 0-.022.144v3.83c0 .45.27.801.626 1.101.358.302.842.572 1.428.804 1.172.46 2.755.776 4.516.776 1.763 0 3.346-.317 4.518-.777.586-.23 1.07-.501 1.428-.803.355-.3.626-.65.626-1.1v-3.83a.456.456 0 0 0-.022-.145l3.264-1.425c.25-.116.25-.59 0-.705L12.13 5.025c-.082-.046-.22-.017-.26 0v.001zm.13.767l8.743 3.804L12 13.392 3.257 9.599l8.742-3.806zm-5.88 5.865l5.75 2.502a.319.319 0 0 0 .26 0l5.75-2.502v3.687c0 .077-.087.262-.358.491-.372.29-.788.52-1.232.68-1.078.426-2.604.743-4.29.743s-3.212-.317-4.29-.742c-.444-.161-.86-.39-1.232-.68-.273-.23-.358-.415-.358-.492v-3.687z"
	_HOME_SVG_PATH = "M19.695 9.518H4.427V21.15h15.268V9.52zM3.109 9.482h17.933L12.06 3.709 3.11 9.482z"
	_LOCATION_SVG_PATH = "M11.436 21.17l-.185-.165a35.36 35.36 0 0 1-3.615-3.801C5.222 14.244 4 11.658 4 9.524 4 5.305 7.267 2 11.436 2c4.168 0 7.437 3.305 7.437 7.524 0 4.903-6.953 11.214-7.237 11.48l-.2.167zm0-18.683c-3.869 0-6.9 3.091-6.9 7.037 0 4.401 5.771 9.927 6.897 10.972 1.12-1.054 6.902-6.694 6.902-10.95.001-3.968-3.03-7.059-6.9-7.059h.001z"
	_DISTANCE_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" focusable="false" role="img" class="Va(tt) Sq(16px)"><title></title><g fill="var(--color--icon-secondary, inherit)"><path fill-rule="evenodd" d="M12.301 23.755c.746-.659 9.449-8.339 9.449-14.337C21.75 4.138 17.463 0 11.998 0 6.534 0 2.25 4.138 2.25 9.418c0 2.675 1.602 5.91 4.769 9.616a45.204 45.204 0 0 0 4.737 4.759l.246.207.26-.21zm-.305-2.424c.94-.889 2.376-2.32 3.77-4.011 1.084-1.315 2.105-2.741 2.847-4.152.753-1.433 1.142-2.705 1.142-3.75 0-4.113-3.328-7.423-7.757-7.423-4.428 0-7.753 3.309-7.753 7.423 0 1.941 1.208 4.713 4.29 8.319a42.901 42.901 0 0 0 3.461 3.594" clip-rule="evenodd"></path><path fill-rule="evenodd" d="M12 6.998a2.002 2.002 0 1 0 0 4.004 2.002 2.002 0 0 0 0-4.005M8.002 9a3.997 3.997 0 1 1 7.995 0 3.997 3.997 0 0 1-7.994 0" clip-rule="evenodd"></path></g></svg>'
	_GENDER_SVG_PATH = "M15.507 13.032c1.14-.952 1.862-2.656 1.862-5.592C17.37 4.436 14.9 2 11.855 2 8.81 2 6.34 4.436 6.34 7.44c0 3.07.786 4.8 2.02 5.726-2.586 1.768-5.054 4.62-4.18 6.204 1.88 3.406 14.28 3.606 15.726 0 .686-1.71-1.828-4.608-4.4-6.338"
	_HEIGHT_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" focusable="false" role="img" class="Va(tt) Sq(16px)"><title></title><g fill="var(--color--icon-secondary, inherit)"><path fill-rule="evenodd" d="M16.95 0a1 1 0 0 1 .707.293l6.05 6.05a1 1 0 0 1 0 1.414l-15.95 15.95a1 1 0 0 1-1.414 0l-6.05-6.05a1 1 0 0 1 0-1.414L16.243.293A1 1 0 0 1 16.95 0M2.414 16.95l4.636 4.636 1.116-1.116-2.318-2.318a1 1 0 1 1 1.414-1.414l2.318 2.317 1.308-1.308-1.15-1.15a1 1 0 1 1 1.414-1.415l1.15 1.151 1.309-1.308-2.318-2.318a1 1 0 0 1 1.414-1.414l2.318 2.318 1.308-1.308-1.151-1.152a1 1 0 0 1 1.414-1.414l1.151 1.151 1.308-1.308-2.317-2.318a1 1 0 0 1 1.414-1.414l2.318 2.318 1.116-1.116-4.636-4.636z" clip-rule="evenodd"></path></g></svg>'
	_SVG_MAP = {
		_HEIGHT_SVG: "height",
		_DISTANCE_SVG: "distance",
		_WORK_SVG: "work",
	}
	def get_row_data(self):
		rowdata = {
			"interests": []
		}
		# return rowdata
		self._open_profile()
    	# iterate this content to find items

		list_items = self.browser.find_elements(By.TAG_NAME, "li")
		for li in list_items:
			if li.text == '':
				continue
			# check for messages
			if len(li.find_elements(By.TAG_NAME, 'a')) > 0:
				continue
			print(li.text)
			# special case for interests:
			try:
				interest = li.find_element(By.XPATH, ".//div/span")
				rowdata["interests"].append(interest.text)
				continue
			except:
				pass
			# special case for q&a
			try:
				q = li.find_element(By.TAG_NAME, "h3").text.lower()
				if q == "How often do you smoke?".lower():
					q = "smoking"
				a = li.find_element(By.XPATH, ".//div/div/div[2]").text
				rowdata[q] = a
				continue
			except:
				pass
			# else, essentials
			svg = li.find_elements(By.TAG_NAME, "svg")
			if len(svg) != 1:
				continue
			svg_val = svg[0].get_attribute('outerHTML')
			value = li.find_element(By.XPATH, ".//div/div/div").text
			
			if self._SVG_MAP.get(svg_val, None) != None:
				category = self._SVG_MAP.get(svg_val)
				rowdata[category] = value
			
				if category == "distance":
					distance = value.replace("kilometres away", "km")
					rowdata['distance'] = distance

		return rowdata

	def get_bio_and_passions(self):
		self._open_profile()

		bio = None
		looking_for = None

		infoItems = {
			"passions": [],
			"lifestyle": [],
			"basics": []
		}

		anthem = None

		lifestyle = []

		# Bio
		try:
			bio = self.browser.find_element(By.XPATH, "//div[@class='C($c-ds-text-primary) Typs(body-1-regular)']").text
		except Exception as e:
			pass

		# Looking for
		try:
			xpath = "//span[@class='Typs(display-3-strong) C($c-ds-text-primary) Mstart(4px)']"
			looking_for = self.browser.find_element(By.XPATH, xpath).text

		except Exception as e:
			pass

		return bio, infoItems["passions"], infoItems["lifestyle"], infoItems[
			"basics"], anthem, looking_for

	def get_images(self):
		self._open_profile()

		images = []
		idx = 0
		while True:
			elements = self.browser.find_elements(By.XPATH, f'//*[@id="carousel-item-{idx}"]/div/div')
			
			# can be more than 1...
			# if len(elements) > 1:
			# 	raise Exception("Expected only 1, wtf")

			if len(elements) == 0:
				break
			
   			# TODO: image parsing fails here
			x =  elements[0].get_attribute("outerHTML")
			q = "&quot;"
			start = x[x.find('url(') + 4 + len(q):]
			image_url = start[:start.find(q)].replace("&amp;", "&")
			images.append(image_url)
			# images += [x.screenshot_as_png for x in elements]
			idx += 1

			action = ActionChains(self.browser)
			action.send_keys(Keys.SPACE).perform()
			time.sleep(1)

		return images


	@staticmethod
	def de_emojify(text):
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


	def get_insta(self, text):
		"""Take the bio and read line by line to match if the description
		contain an instagram user.
		Args:
			text (string): string with emojis or not
		Returns:
			ig (string): return valid instagram user.
		"""
		if not text:
			return None
		valid_pattern = [
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
		description = text.rstrip().lower().strip()
		description = description.split()
		for x in range(len(description)):
			ig = self.de_emojify(description[x])
			if '@' in ig:
				return ig.replace('@', '')
			elif ig in valid_pattern:
				try:
					if ':' in description[x + 1]:
						return description[x + 2]
					else:
						return description[x + 1]
				except:
					return None
			else:
				try:
					ig = ig.split(':', 1)
					if ig[0] in valid_pattern:
						return ig[-1]
				except:
					return None
		return None


	def _get_home_page(self):
		self.browser.get(self.HOME_URL)
		time.sleep(10)


	def _is_profile_opened(self):
		return self.opened_profile
		if '/profile' in self.browser.current_url:
			return True
		else:
			return False
