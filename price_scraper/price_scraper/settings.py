import copy

import scrapy.utils.log
from colorlog import ColoredFormatter

# --- Logging Configuration ---
_color_formatter = ColoredFormatter(
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
    if handler:
        handler.setFormatter(_color_formatter)
    return handler


scrapy.utils.log._get_handler = _get_handler_custom
# --- End Logging Configuration ---


# --- Project Identification ---
BOT_NAME = "price_scraper"  # Project name
SPIDER_MODULES = ["price_scraper.spiders"]
NEWSPIDER_MODULE = "price_scraper.spiders"
# --- End Project Identification ---


# --- Core Scrapy Settings ---
ROBOTSTXT_OBEY = True
LOG_LEVEL = "DEBUG"
LOG_ENABLED = True
# Define the log file path
# LOG_FILE = "output/scrapy_run.log"  # Log file will be in the 'output' directory

# Set to False to overwrite the log file each time, True to append
# LOG_FILE_APPEND = False

# Standard log format for files (adjust as needed)
# LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
# LOG_DATEFORMAT = "%Y-%m-%d %H:%M:%S"  # Consistent date format
COOKIES_ENABLED = False
TELNETCONSOLE_ENABLED = False
# --- End Core Scrapy Settings ---


# --- Concurrency and Throttling (Reasonable Defaults) ---
CONCURRENT_REQUESTS = 32
CONCURRENT_REQUESTS_PER_DOMAIN = 16

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 8.0
AUTOTHROTTLE_MAX_DELAY = 60.0
# --- End Concurrency and Throttling ---


# --- HTTP Cache (Development Only!) ---
HTTPCACHE_ENABLED = True
HTTPCACHE_DIR = "httpcache"
HTTPCACHE_IGNORE_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]
HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"
HTTPCACHE_EXPIRATION_SECS = 0
# --- End HTTP Cache ---


# --- Middlewares ---
DOWNLOADER_MIDDLEWARES = {
    "price_scraper.middlewares.UserAgentRotatorMiddleware": 450,
    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
    "price_scraper.middlewares.CustomRetryMiddleware": 540,
    "scrapy.downloadermiddlewares.httpcache.HttpCacheMiddleware": 900,
}

# --- End Middlewares ---


# --- Item Pipelines (Order Matters!) ---
ITEM_PIPELINES = {
    "price_scraper.pipelines.DropDuplicatesPipeline": 100,
    "price_scraper.pipelines.RequiredFieldsPipeline": 200,
    "price_scraper.pipelines.JsonLinesExportPipeline": 800,
}
# --- End Item Pipelines ---


# --- Extension Configuration ---
EXTENSIONS = {
    "price_scraper.extensions.runtime_extension.RuntimeLogger": 500,
}
RUNTIME_LOGGER_ENABLED = True
# --- End Extension Configuration ---
