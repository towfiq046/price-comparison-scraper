import logging

from scrapy import signals
from scrapy.exceptions import NotConfigured


class RuntimeLogger:
    """
    A Scrapy extension to log the runtime of a spider.
    """

    def __init__(self, crawler):
        """
        Initialize the RuntimeLogger extension.
        """
        self.crawler = crawler
        self.start_time = None
        crawler.signals.connect(self.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(self.spider_closed, signal=signals.spider_closed)

    @classmethod
    def from_crawler(cls, crawler):
        """
        Create an instance of RuntimeLogger from the crawler.
        """
        if not crawler.settings.getbool("RUNTIME_LOGGER_ENABLED"):
            raise NotConfigured
        return cls(crawler)

    def spider_opened(self, spider):
        """
        Log the start time of the spider.
        """
        self.start_time = self.crawler.stats.get_value("start_time")
        if self.start_time:
            spider.logger.info("Spider started at %s", self.start_time)
        else:
            spider.logger.error("Start time is missing in stats.")

    def spider_closed(self, spider):
        """
        Log the finish time and total runtime of the spider.
        """
        finish_time = self.crawler.stats.get_value("finish_time")
        if not self.start_time or not finish_time:
            spider.logger.error("Unable to calculate runtime: start_time or finish_time is missing.")
            return

        runtime = finish_time - self.start_time
        runtime_seconds = runtime.total_seconds()
        minutes, seconds = divmod(runtime_seconds, 60)
        spider.logger.info(
            "Spider finished at %s. Total runtime: %d minutes and %.2f seconds", finish_time, int(minutes), seconds
        )
