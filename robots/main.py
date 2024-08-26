from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import os
import requests
import logging
import yaml

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsScraperBot:
    def __init__(self, url, search_phrase=None, category=None, months=1):
        self.driver = webdriver.Chrome()
        self.url = url
        self.search_phrase = search_phrase
        self.category = category
        self.months = months
        self.news_data = []

    def open_website_and_search(self):
        logger.info(f"Opening website: {self.url}")
        self.driver.get(self.url)

        try:
            logger.info("Waiting for the search button to be clickable")
            search_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-element="search-button"]'))
            )
            search_button.click()
        except Exception as e:
            logger.error(f"Failed to find the search button: {e}")
            self.driver.save_screenshot("output/button_to_search_bar_error.png")

        try:
            logger.info(f"Waiting for the search input to be available")
            search_input = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[data-element="search-form-input"]'))
            )
            search_input.send_keys(self.search_phrase)
        except Exception as e:
            logger.error(f"Failed to find the search input: {e}")
            self.driver.save_screenshot("output/search_bar_error.png")

        try:
            logger.info("Waiting for the search submit button to be clickable")
            submit_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-element="search-submit-button"]'))
            )
            submit_button.click()
        except Exception as e:
            logger.error(f"Failed to find the submit button: {e}")
            self.driver.save_screenshot("output/submit_button_error.png")

    def filter_by_category(self):
        if self.category:
            logger.info(f"Filtering results by category: {self.category}")
            try:
                category_element = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, f'//a[contains(text(), "{self.category}")]'))
                )
                category_element.click()
            except Exception as e:
                logger.error(f"Failed to filter by category: {e}")
                self.driver.save_screenshot("output/category_filter_error.png")

    def extract_news_data(self):
        logger.info("Extracting news data")
        try:
            titles = self.driver.find_elements(By.XPATH, '//h3[contains(@class, "title")]')
            dates = self.driver.find_elements(By.XPATH, '//time[contains(@class, "date")]')
            descriptions = self.driver.find_elements(By.XPATH, '//p[contains(@class, "description")]')
            image_elements = self.driver.find_elements(By.XPATH, '//img[contains(@class, "image-class")]')

            for i in range(len(titles)):
                title = titles[i].text
                date = dates[i].get_attribute("datetime")
                description = descriptions[i].text
                image_url = image_elements[i].get_attribute("src")

                image_filename = self.download_image(image_url, f"output/image_{i}.jpg")
                phrase_count = self.count_phrase_in_text(title, description)
                contains_money = self.check_for_money(title, description)

                self.news_data.append({
                    "title": title,
                    "date": date,
                    "description": description,
                    "image_filename": image_filename,
                    "phrase_count": phrase_count,
                    "contains_money": contains_money,
                })

                logger.info(f"Extracted news: {title} | Date: {date} | Money mentioned: {contains_money}")
        except Exception as e:
            logger.error(f"Failed to extract news data: {e}")
            self.driver.save_screenshot("output/extract_news_data_error.png")

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
        phrase_count = title.lower().count(self.search_phrase.lower()) + description.lower().count(self.search_phrase.lower())
        logger.info(f"Phrase '{self.search_phrase}' found {phrase_count} times in the title and description")
        return phrase_count

    def check_for_money(self, title, description):
        money_pattern = r"(\$\d+[\.,]?\d*)|(\d+ dollars)|(USD\s?\d+)"
        contains_money = bool(re.search(money_pattern, title + " " + description))
        logger.info(f"Money mentioned in news: {contains_money}")
        return contains_money

    def save_to_excel(self, filename="output/news_data.xlsx"):
        logger.info(f"Saving data to Excel file: {filename}")
        import pandas as pd

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
            self.category = params.get("news_category")
            self.months = int(params.get("months", 1))
        else:
            logger.info("Loading parameters manually")
            # Set parameters manually here
            self.search_phrase = "Your search phrase"
            self.category = "Your category"
            self.months = 1

        logger.info(f"Parameters loaded - Search Phrase: {self.search_phrase}, Category: {self.category}, Months: {self.months}")

    def run(self):
        try:
            self.load_workitem_parameters(local_test=True)
            self.open_website_and_search()
            self.filter_by_category()
            self.extract_news_data()
            self.save_to_excel()
        except Exception as e:
            logger.error(f"An error occurred: {e}")
        finally:
            self.close_browser()
