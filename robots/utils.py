import time
import yaml
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from .logger_config import logger


def retry_with_fallback(func, retries=3, delay=5, *args, **kwargs):
    """Retry a function with specified retries and delay."""
    attempt = 0
    while attempt < retries:
        try:
            return func(*args, **kwargs)
        except (NoSuchElementException, TimeoutException) as e:
            logger.warning(
                f"Attempt {attempt + 1} failed with error: {e}. Retrying in {delay} seconds."
            )
            attempt += 1
            time.sleep(delay)
    logger.error(f"Failed after {retries} attempts.")
    raise Exception(f"Function {func.__name__} failed after {retries} retries.")


def load_local_work_item(file_path):
    """Load work item parameters from a local YAML file."""
    with open(file_path, "r") as file:
        return yaml.safe_load(file)
    
