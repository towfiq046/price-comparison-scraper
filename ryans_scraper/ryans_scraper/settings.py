BOT_NAME = "ryans_scraper"

SPIDER_MODULES = ["ryans_scraper.spiders"]
NEWSPIDER_MODULE = "ryans_scraper.spiders"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 2
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8

FEEDS = {
    "laptops_2pages.json": {
        "format": "json",
        "overwrite": True,
    }
}

LOG_ENABLED = True
LOG_LEVEL = "DEBUG"
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
            "level": "DEBUG",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "scrapy": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
