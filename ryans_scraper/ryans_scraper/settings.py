import copy

import scrapy.utils.log
from colorlog import ColoredFormatter


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

# Store the original handler retrieving function
_get_handler = copy.copy(scrapy.utils.log._get_handler)


# Define the wrapper function that applies the formatter
def _get_handler_custom(*args, **kwargs):
    """Retrieves Scrapy's default handler and applies the custom color formatter."""
    handler = _get_handler(*args, **kwargs)
    if handler:  # Ensure handler was actually created
        handler.setFormatter(_color_formatter)
    return handler


# Apply the monkeypatch globally for Scrapy's logging setup
scrapy.utils.log._get_handler = _get_handler_custom

BOT_NAME = "ryans_laptops_lite"
SPIDER_MODULES = ["ryans_scraper.spiders"]
NEWSPIDER_MODULE = "ryans_scraper.spiders"

LOG_LEVEL = "DEBUG"
LOG_ENABLED = True

ROBOTSTXT_OBEY = True

CONCURRENT_REQUESTS = 8  # Reduced from 16. More polite baseline, less resource intensive.

# Enable AutoThrottle for adaptive delays (Highly Recommended)
AUTOTHROTTLE_ENABLED = True
# The average number of requests Scrapy should be sending in parallel *to each domain*.
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0  # Polite setting, aiming for 1 request at a time per domain.
# Initial download delay (seconds). AutoThrottle starts here and adjusts.
AUTOTHROTTLE_START_DELAY = 1.0  # Start with a 1-second delay.
# Maximum download delay (seconds) if server latency is high.
AUTOTHROTTLE_MAX_DELAY = 30.0
# AUTOTHROTTLE_DEBUG = True # Uncomment to see detailed throttling logs

# DOWNLOAD_DELAY = 1 # Commented out: Redundant and potentially confusing when AutoThrottle is enabled.
# AutoThrottle manages delays dynamically based on TARGET_CONCURRENCY.

# Configure concurrent requests performed per domain (Alternative if AUTOTHROTTLE_ENABLED=False)
# CONCURRENT_REQUESTS_PER_DOMAIN = 1

# Configure concurrent requests performed per IP (requires setting DOWNLOADER_CLIENTCONTEXTFACTORY)
# CONCURRENT_REQUESTS_PER_IP = 1

DOWNLOADER_MIDDLEWARES = {
    "ryans_scraper.middlewares.UserAgentRotatorMiddleware": 543,
    "ryans_scraper.middlewares.CustomRetryMiddleware": 550,
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": None
}

ITEM_PIPELINES = {
    "ryans_scraper.pipelines.LaptopValidationPipeline": 300,
    "ryans_scraper.pipelines.JsonLinesExportPipeline": 400,
}

EXTENSIONS = {
    "ryans_scraper.extensions.runtime_extension.RuntimeLogger": 500,
}

RUNTIME_LOGGER_ENABLED = True


# --- Optional Settings ---

COOKIES_ENABLED = False  # Uncomment if you don't need cookie handling
TELNETCONSOLE_ENABLED = False  # Disable if not needed (security best practice)
HTTPCACHE_ENABLED = True  # Strongly recommend enabling during development/debugging
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_EXPIRATION_SECS = 0 # Cache forever (during dev)
