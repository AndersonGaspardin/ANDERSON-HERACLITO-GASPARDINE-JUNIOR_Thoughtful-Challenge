from datetime import datetime
import requests

from RPA.Browser.Selenium import Selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd

import re
import os
import yaml

from robots.utils import retry_with_fallback
from .logger_config import logger


class NewsScraperBot:
    def __init__(self, url, search_phrase=None, category=None, months=1):
        self.browser = Selenium()
        self.driver = ""
        self.url = url
        self.search_phrase = search_phrase
        self.category = category
        self.months = months
        self.news_data = []
        self.retry_website = "https://www.latimes.com/search?q="

    def open_website(self):
        logger.info(f"Opening website: {self.url}")
        self.browser.open_available_browser(self.url)
        self.driver = self.browser.driver

    def search(self):
        self.wait_for_page_load()
        try:
            logger.info("Waiting for the search button to be clickable")
            search_button = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        "body > ps-header > header > div.flex.\[\@media_print\]\:hidden > button",
                    )
                )
            )
            search_button.click()
        except Exception as e:
            logger.error(f"Failed to find the search button: {e}")
            self.driver.save_screenshot("output/button_to_search_bar_error.png")
        try:
            self.wait_for_page_load()
            logger.info(f"Waiting for the search input to be available")
            search_input = WebDriverWait(self.driver, 60).until(
                EC.visibility_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "body > ps-header > header > div.flex.\[\@media_print\]\:hidden > div.ct-hidden.fixed.md\:absolute.top-12\.5.right-0.bottom-0.left-0.z-25.bg-header-bg-color.md\:top-15.md\:bottom-auto.md\:h-25.md\:shadow-sm-2 > form > label > input",
                    )
                )
            )
            search_input.send_keys(self.search_phrase)
            search_input.submit()

        except Exception as e:
            logger.error(f"Failed to find the search input: {e}")
            self.driver.save_screenshot("output/search_bar_error.png")

    def filter_by_category(self):
        if self.category:
            logger.info(f"Filtering results by category: {self.category}")
            self.wait_for_page_load()
            try:
                logger.info("Ensuring all filters are visible")
                see_all_locator = '//button[@data-toggle-trigger="see-all"]'
                see_all_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, see_all_locator))
                )
                retry_with_fallback(
                    lambda: see_all_button.click(),
                    retries=3,
                    delay=5,
                )
                logger.info(
                    f"Looking for category '{self.category}' in the filter list"
                )
                category_elements = self.driver.find_elements(
                    By.XPATH,
                    '//li//div[contains(@class, "search-filter-input")]//label//span',
                )

                for element in category_elements:
                    if self.category.lower() in element.text.lower():
                        checkbox = element.find_element(
                            By.XPATH, '../input[@type="checkbox"]'
                        )
                        retry_with_fallback(
                            lambda: checkbox.click(),
                            retries=3,
                            delay=5,
                        )
                        logger.info(
                            f"Category '{self.category}' selected successfully."
                        )
                        return

            except Exception as e:
                logger.error(f"Failed to filter by category '{self.category}': {e}")
                self.driver.save_screenshot("output/category_filter_error.png")

    def sort_by_newest(self):
        logger.info("Sorting results by newest")
        self.wait_for_page_load()
        try:
            sort_locator = "select.select-input"
            sort_dropdown = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, sort_locator))
            )
            sort_dropdown.click()

            newest_option_locator = 'option[value="1"]'
            newest_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, newest_option_locator))
            )
            newest_option.click()

            logger.info("Sorted results by newest")
        except Exception as e:
            logger.error(f"Failed to sort by newest: {e}")
            self.driver.save_screenshot("output/sort_by_newest_error.png")

    def extract_news_data(self):
        logger.info("Extracting news data")
        wait = WebDriverWait(self.browser.driver, 30)
        try:
            while True:
                self.wait_for_page_load(timeout=30)
                titles_locator = '//h3[contains(@class, "title")]'
                dates_locator = '//p[@class="promo-timestamp"]'
                description_locator = '//p[contains(@class, "description")]'
                image_locator = '//img[contains(@class, "image")]'

                titles = retry_with_fallback(
                    lambda: wait.until(
                        EC.visibility_of_all_elements_located(
                            (By.XPATH, titles_locator)
                        )
                    )
                )
                dates = retry_with_fallback(
                    lambda: wait.until(
                        EC.visibility_of_all_elements_located(
                            (By.XPATH, dates_locator)
                        )
                    )
                )
                descriptions = retry_with_fallback(
                    lambda: wait.until(
                        EC.visibility_of_all_elements_located(
                            (By.XPATH, description_locator)
                        )
                    )
                )
                image_elements = retry_with_fallback(
                    lambda: wait.until(
                        EC.visibility_of_all_elements_located(
                            (By.XPATH, image_locator)
                        )
                    )
                )

                for i in range(len(titles)):
                    title = titles[i].text if titles[i] else ""

                    date_text = (
                        dates[i].get_attribute("data-timestamp") if dates[i] else ""
                    )
                    date = self.convert_timestamp_to_date(date_text)

                    description = descriptions[i].text if descriptions[i] else ""

                    image_url = (
                        image_elements[i].get_attribute("src")
                        if image_elements[i]
                        else ""
                    )
                    image_filename = (
                        self.download_image(
                            image_url, f"output/image_{date}_{i}.jpg"
                        )
                        if image_url
                        else ""
                    )

                    phrase_count = self.count_phrase_in_text(title, description)
                    contains_money = self.check_for_money(title, description)

                    if (datetime.now() - date).days / 30 > self.months:
                        logger.info(
                            "News articles are older than the specified months."
                        )
                        return

                    self.news_data.append(
                        {
                            "title": title,
                            "date": date.strftime("%Y-%m-%d"),
                            "description": description,
                            "image_filename": image_filename,
                            "phrase_count": phrase_count,
                            "contains_money": contains_money,
                        }
                    )

                    logger.info(
                        f"Extracted news: {title} | Date: {date} | Money mentioned: {contains_money}"
                    )

                try:
                    next_button_locator = "div.search-results-module-next-page a"
                    next_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, next_button_locator)
                        )
                    )
                    next_button.click()
                    logger.info("Navigating to the next page.")
                except Exception as e:
                    logger.info("No more pages to navigate.")
                    break

        except Exception as e:
            logger.error(f"Failed to extract news data: {e}")
            self.driver.save_screenshot("output/extract_news_data_error.png")

    def convert_timestamp_to_date(self, timestamp):
        """Convert a timestamp to a datetime object."""
        try:
            return datetime.fromtimestamp(int(timestamp) / 1000)
        except ValueError:
            logger.error(f"Invalid timestamp: {timestamp}")
            return datetime.min

    def download_image(self, url, file_path):
        logger.info(f"Downloading image from: {url}")
        try:
            response = requests.get(url)
            with open(file_path, "wb") as file:
                file.write(response.content)
            logger.info(f"Image saved as: {file_path}")
            return os.path.basename(file_path)
        except Exception as e:
            logger.error(f"Failed to download image from {url}. Error: {e}")
            return None

    def count_phrase_in_text(self, title, description):
        phrase_count = title.lower().count(
            self.search_phrase.lower()
        ) + description.lower().count(self.search_phrase.lower())
        logger.info(
            f"Phrase '{self.search_phrase}' found {phrase_count} times in the title and description"
        )
        return phrase_count

    def check_for_money(self, title, description):
        money_pattern = r"(\$\d+[\.,]?\d*)|(\d+ dollars)|(USD\s?\d+)"
        contains_money = bool(re.search(money_pattern, title + " " + description))
        logger.info(f"Money mentioned in news: {contains_money}")
        return contains_money

    def save_to_excel(self, filename="output/news_data.xlsx"):
        logger.info(f"Saving data to Excel file: {filename}")

        df = pd.DataFrame(self.news_data)
        df.to_excel(filename, index=False)
        logger.info("Data saved successfully")

    def close_browser(self):
        logger.info("Closing browser")
        self.driver.quit()

    def load_workitem_parameters(self, local_test=False):
        """Load parameters from a local file for testing or set manually."""
        if local_test:
            logger.info("Loading parameters from local file")
            with open("work_item.yaml", "r") as file:
                params = yaml.safe_load(file)
            self.search_phrase = params.get("search_phrase")
            self.category = params.get("news_category", None)
            self.months = int(params.get("months", 1))
        else:
            logger.info("Loading parameters manually")
            # Set parameters manually here
            self.search_phrase = "Your search phrase"
            self.category = "Your category"
            self.months = 1

        logger.info(
            f"Parameters loaded - Search Phrase: {self.search_phrase}, Category: {self.category}, Months: {self.months}"
        )

    def wait_for_page_load(self, timeout=10):
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState")
                == "complete"
            )
            logger.info("Page has fully loaded.")
        except Exception as e:
            logger.error(f"Page did not load within {timeout} seconds. Error: {e}")

    def run(self):
        try:
            self.load_workitem_parameters(local_test=True)
            self.open_website()
            self.search()
            if self.category:
                self.filter_by_category()
            self.sort_by_newest()
            self.extract_news_data()
            self.save_to_excel()
        except Exception as e:
            logger.error(f"An error occurred: {e}")
        finally:
            self.close_browser()
