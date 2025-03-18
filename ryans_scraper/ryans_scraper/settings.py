from datetime import datetime

BOT_NAME = "ryans_laptops"

SPIDER_MODULES = ["ryans_scraper.spiders"]
NEWSPIDER_MODULE = "ryans_scraper.spiders"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
ROBOTSTXT_OBEY = True  # Set to False if legally/ethically permissible for your use case
DOWNLOAD_DELAY = 1
RANDOMIZE_DOWNLOAD_DELAY = True
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
DOWNLOAD_TIMEOUT = 30
RETRY_ENABLED = True
RETRY_TIMES = 3
HTTPERROR_ALLOWED_CODES = [403, 404]


FEEDS = {
    f"laptops_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json": {
        "format": "json",
        "overwrite": False,
    }
}

LOG_ENABLED = True
LOG_LEVEL = "DEBUG"  # Use "DEBUG" only for troubleshooting
# LOG_FILE = "scrapy.log"
# LOG_FILE_APPEND = False

RUNTIME_LOGGER_ENABLED = True
EXTENSIONS = {
    "ryans_scraper.extensions.runtime_extension.RuntimeLogger": 100,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "colored": {
            "()": "colorlog.ColoredFormatter",
            "format": "%(log_color)s%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "log_colors": {
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "colored",
            "level": "INFO",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "scrapy": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Optional: Add proxy support if needed
# DOWNLOADER_MIDDLEWARES = {
#     'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
#     'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
#     'rotating_proxies.middlewares.BanDetectionMiddleware': 620,
# }
# ROTATING_PROXY_LIST = ['proxy1:port', 'proxy2:port', ...]
