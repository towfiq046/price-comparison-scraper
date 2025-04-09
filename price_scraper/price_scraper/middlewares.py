import logging
import random
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message


class UserAgentRotatorMiddleware:
    """
    Middleware to rotate User-Agents for requests to avoid detection.
    Compatible with ryans.com and respects rate limits via settings.
    """

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    ]

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_request(self, request, spider):
        """Set a random User-Agent for each request."""
        ua = random.choice(self.user_agents)
        request.headers["User-Agent"] = ua
        self.logger.debug(f"Using User-Agent: {ua} for {request.url}")
        return None


class CustomRetryMiddleware(RetryMiddleware):
    """
    Custom retry middleware to handle failed requests (e.g., 403, 429).
    Works with ryans.com and respects AUTOTHROTTLE_ENABLED.
    """

    def __init__(self, settings):
        super().__init__(settings)
        self.logger = logging.getLogger(__name__)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_response(self, request, response, spider):
        """Retry on 403 or 429 status codes."""
        if response.status in [403, 429]:
            self.logger.warning(f"Received {response.status} for {request.url}. Retrying...")
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response
        return response

    def process_exception(self, request, exception, spider):
        """Retry on network exceptions."""
        self.logger.warning(f"Exception {exception} for {request.url}. Retrying...")
        return self._retry(request, exception, spider)
