from robots import NewsScraperBot

def main():
    bot = NewsScraperBot(
        url="https://www.latimes.com/", search_phrase=None, category=None, months=1
    )
    bot.run()


if __name__ == "__main__":
    main()
