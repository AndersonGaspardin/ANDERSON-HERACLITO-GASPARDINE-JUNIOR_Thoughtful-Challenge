from RPA.Browser.Selenium import Selenium
from RPA.Excel.Files import Files
from RPA.Robocorp.WorkItems import WorkItems
import re
import os
import requests
from utils import retry_with_fallback
from logger_config import setup_logging

logger = setup_logging()


class NewsScraperBot:
    def __init__(self, url, search_phrase=None, category=None, months=1):
        self.browser = Selenium()
        self.excel = Files()
        self.workitems = WorkItems()
        self.url = url
        self.search_phrase = search_phrase
        self.category = category
        self.months = months
        self.news_data = []

    def open_website_and_search(self):
        logger.info(f"Opening website: {self.url}")
        self.browser.open_available_browser(self.url)
        logger.info(f"Searching for phrase: {self.search_phrase}")
        retry_with_fallback(
            self.browser.input_text,
            retries=3,
            delay=5,
            *'input[name="q"]',
            *self.search_phrase,
        )
        retry_with_fallback(
            self.browser.press_keys, retries=3, delay=5, *'input[name="q"]', *"ENTER"
        )

    def filter_by_category(self):
        if self.category:
            logger.info(f"Filtering results by category: {self.category}")
            retry_with_fallback(
                self.browser.click_element,
                retries=3,
                delay=5,
                *f'//a[contains(text(), "{self.category}")]',
            )

    def extract_news_data(self):
        logger.info("Extracting news data")
        titles = retry_with_fallback(
            lambda: self.browser.find_elements('//h3[contains(@class, "title")]'),
            retries=3,
            delay=5,
        )
        dates = retry_with_fallback(
            lambda: self.browser.find_elements('//time[contains(@class, "date")]'),
            retries=3,
            delay=5,
        )
        descriptions = retry_with_fallback(
            lambda: self.browser.find_elements(
                '//p[contains(@class, "description")]'
            ),
            retries=3,
            delay=5,
        )
        image_elements = retry_with_fallback(
            lambda: self.browser.find_elements(
                '//img[contains(@class, "image-class")]'
            ),
            retries=3,
            delay=5,
        )

        for i in range(len(titles)):
            title = titles[i].text
            date = dates[i].get_attribute("datetime")
            description = descriptions[i].text
            image_url = image_elements[i].get_attribute("src")

            image_filename = self.download_image(image_url, f"output/image_{i}.jpg")

            phrase_count = self.count_phrase_in_text(title, description)

            contains_money = self.check_for_money(title, description)

            self.news_data.append(
                {
                    "title": title,
                    "date": date,
                    "description": description,
                    "image_filename": image_filename,
                    "phrase_count": phrase_count,
                    "contains_money": contains_money,
                }
            )

            logger.info(
                f"Extracted news: {title} | Date: {date} | Money mentioned: {contains_money}"
            )

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
        self.excel.create_workbook(filename)
        self.excel.append_rows_to_worksheet(self.news_data, header=True)
        self.excel.save_workbook()
        logger.info("Data saved successfully")

    def close_browser(self):
        logger.info("Closing browser")
        self.browser.close_all_browsers()

    def load_workitem_parameters(self):
        logger.info("Loading parameters from Work Item")
        self.workitems.get_input_work_item()

        self.search_phrase = self.workitems.get_work_item_variable("search_phrase")
        self.category = self.workitems.get_work_item_variable("news_category")
        self.months = int(self.workitems.get_work_item_variable("months"))

        logger.info(
            f"Parameters loaded - Search Phrase: {self.search_phrase}, Category: {self.category}, Months: {self.months}"
        )

    def run(self):
        try:
            self.load_workitem_parameters()
            self.open_website_and_search()
            self.filter_by_category()
            self.extract_news_data()
            self.save_to_excel()
        except Exception as e:
            logger.error(f"An error occurred: {e}")
        finally:
            self.close_browser()



