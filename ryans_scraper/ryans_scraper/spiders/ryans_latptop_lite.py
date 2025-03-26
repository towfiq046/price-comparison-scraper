import logging

from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from scrapy.spiders import CrawlSpider, Rule

from ryans_scraper.items import LaptopItem


class RyansLaptopsSpider(CrawlSpider):
    name = "ryans_laptops_lite"
    allowed_domains = ["ryans.com"]
    start_urls = ["https://www.ryans.com/category/laptop-all-laptop?limit=100"]

    rules = [Rule(LinkExtractor(allow=r"limit=100&page=\d+"), callback="parse_category", follow=True)]

    IMAGE_BOX_XPATH = ".//div[contains(@class, 'image-box')]//a/@href"
    NAME_XPATH = ".//p[contains(@class, 'card-text')]//a/@title"
    PRICE_XPATH = ".//a[contains(@class, 'pr-text')]/text()"
    IMAGE_XPATH = ".//div[contains(@class, 'image-box')]//img/@src"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger.setLevel(logging.DEBUG)

    def parse_category(self, response):
        """Parse category pages and extract product data."""
        self.logger.debug(f"Parsing category page: {response.url}")
        self._log_response_details(response)

        cards = response.xpath("//div[contains(@class, 'card') and contains(@class, 'h-100')]")
        self.logger.info(f"Page: {response.url} | Found {len(cards)} product cards")

        if not cards:
            self.logger.warning(f"Page: {response.url} | No cards found! Check XPath or page structure.")
            return

        for card in cards:
            product = self._extract_product(card)
            yield product

        self._log_pagination_links(response)

    def _extract_product(self, card):
        """Extract product data from a card using ItemLoader."""
        loader = ItemLoader(item=LaptopItem(), selector=card)

        loader.add_xpath("url", self.IMAGE_BOX_XPATH)
        loader.add_xpath("name", self.NAME_XPATH, default="")
        loader.add_xpath("price", self.PRICE_XPATH, default="")
        loader.add_xpath("image", self.IMAGE_XPATH)

        product = loader.load_item()
        # self.logger.debug(f"Extracted product: {dict(product)}")
        self._validate_product(product, card)
        return product

    def _validate_product(self, product, card):
        """Log warnings for missing fields."""
        for field in ["url", "name", "price", "image"]:
            if not product.get(field):
                self.logger.warning(f"Missing {field} in card: {card.extract()[:200]}")

    def _log_response_details(self, response):
        """Log response status and snippet for debugging."""
        self.logger.debug(f"Response status: {response.status}")
        self.logger.debug(f"Response snippet: {response.text[:500]}")

    def _log_pagination_links(self, response):
        """Log pagination links for debugging."""
        pagination_links = response.xpath("//a[contains(@href, 'limit=100&page=')]/@href").getall()
        self.logger.debug(f"Page: {response.url} | Pagination links: {pagination_links}")
