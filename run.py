from robots import NewsScraperBot


if __name__ == "__main__":
    bot = NewsScraperBot(
        url="https://www.reuters.com/", search_phrase=None, category=None, months=1
    )
    bot.run()