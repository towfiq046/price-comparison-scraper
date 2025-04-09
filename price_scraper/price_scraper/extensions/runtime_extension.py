import logging
from datetime import datetime
from scrapy import signals
from scrapy.exceptions import NotConfigured
from scrapy.statscollectors import StatsCollector


class RuntimeLogger:
    """
    A Scrapy extension to log the start time, finish time,
    finish reason, and total runtime of a spider.
    """

    def __init__(self, stats: StatsCollector):
        """
        Initialize the RuntimeLogger extension.

        Args:
            stats: The Scrapy stats collector instance.
        """
        self.stats = stats
        self.logger = logging.getLogger(__name__)
        self.start_time: datetime | None = None

    @classmethod
    def from_crawler(cls, crawler):
        """
        Factory method to create an instance, connecting signals.
        Checks if the extension is enabled in settings.
        """
        if not crawler.settings.getbool("RUNTIME_LOGGER_ENABLED", True):
            raise NotConfigured("RuntimeLogger extension is disabled by setting.")

        ext = cls(crawler.stats)

        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)

        ext.logger.debug("RuntimeLogger initialized and signals connected.")
        return ext

    def spider_opened(self, spider):
        """
        Called when the spider is opened. Logs the start time.
        """
        self.start_time = self.stats.get_value("start_time")

        if isinstance(self.start_time, datetime):
            # start_time_str = self.start_time.isoformat(sep=" ", timespec="seconds")
            start_time_str = self.start_time.astimezone().strftime("%Y-%m-%d %I:%M:%S %p")
            self.logger.info(f"Spider '{spider.name}' started at {start_time_str}")
        else:
            self.logger.error(
                f"Spider '{spider.name}': Could not retrieve valid start time from stats "
                f"(Value: {self.start_time}, Type: {type(self.start_time)})."
            )

    def spider_closed(self, spider, reason: str):
        """
        Called when the spider is closed. Logs finish time, reason, and runtime.
        """
        finish_time = self.stats.get_value("finish_time")

        if not isinstance(self.start_time, datetime) or not isinstance(finish_time, datetime):
            self.logger.error(
                f"Spider '{spider.name}': Unable to calculate runtime - "
                f"start_time ({type(self.start_time)}) or finish_time ({type(finish_time)}) missing or invalid."
            )
            if isinstance(finish_time, datetime):
                # finish_time_str = finish_time.isoformat(sep=" ", timespec="seconds")
                finish_time_str = finish_time.astimezone().strftime("%Y-%m-%d %I:%M:%S %p")
                self.logger.info(f"Spider '{spider.name}' finished at {finish_time_str}. Reason: {reason}.")
            else:
                self.logger.info(f"Spider '{spider.name}' finished. Reason: {reason}.")
            return

        runtime = finish_time - self.start_time
        # finish_time_str = finish_time.isoformat(sep=" ", timespec="seconds")
        finish_time_str = finish_time.astimezone().strftime("%Y-%m-%d %I:%M:%S %p")

        self.logger.info(
            f"Spider '{spider.name}' finished at {finish_time_str}. Reason: {reason}. Total runtime: {runtime}"
        )
