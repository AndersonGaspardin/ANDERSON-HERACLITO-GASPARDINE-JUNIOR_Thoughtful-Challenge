import logging


def setup_logging(log_file="output/news_scraper.log"):
    """Configures the logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )
    logger = logging.getLogger(__name__)
    return logger

logger = setup_logging()