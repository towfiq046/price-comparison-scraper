import copy

import scrapy.utils.log
from colorlog import ColoredFormatter

color_formatter = ColoredFormatter(
    (
        "%(log_color)s%(levelname)-8s%(reset)s "
        "%(yellow)s[%(asctime)s]%(reset)s"
        "%(white)s %(name)s %(funcName)s %(bold_purple)s:%(lineno)d%(reset)s "
        "%(log_color)s%(message)s%(reset)s"
    ),
    datefmt="%d-%m-%y %H:%M:%S",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "bold_red",
        "CRITICAL": "red,bg_white",
    },
)

_get_handler = copy.copy(scrapy.utils.log._get_handler)


def _get_handler_custom(*args, **kwargs):
    handler = _get_handler(*args, **kwargs)
    handler.setFormatter(color_formatter)
    return handler


scrapy.utils.log._get_handler = _get_handler_custom


BOT_NAME = "ryans_laptops_lite"

SPIDER_MODULES = ["ryans_scraper.spiders"]  # Without it Scrapy won't find our spiders

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
# LOG_LEVEL = "DEBUG"  # Detailed logging
LOG_ENABLED = True
CONCURRENT_REQUESTS = 16  # Moderate concurrency
DOWNLOAD_DELAY = 1  # Avoid overwhelming server
AUTOTHROTTLE_ENABLED = True  # Prevent bans
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
ROBOTSTXT_OBEY = True  # Respect robots.txt

FEEDS = {
    "laptops_lite.json": {
        "format": "json",
        "overwrite": True,
    }
}

EXTENSIONS = {
    "ryans_scraper.extensions.runtime_extension.RuntimeLogger": 500,
}

RUNTIME_LOGGER_ENABLED = True
