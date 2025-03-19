import logging
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.exceptions import CloseSpider


class RyansLaptopsSpider(CrawlSpider):
    name = "ryans_laptops_lite"
    allowed_domains = ["ryans.com"]
    start_urls = ["https://www.ryans.com/category/laptop-all-laptop?limit=100"]

    rules = (Rule(LinkExtractor(allow=r"limit=100&page=\d+"), callback="parse_category", follow=True),)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logging.getLogger().setLevel(logging.DEBUG)

    def parse_category(self, response):
        self.logger.debug(f"Parsing category page: {response.url}")

        self.logger.debug(f"Response status: {response.status}")
        self.logger.debug(f"Response snippet: {response.text[:500]}")

        cards = response.xpath("//div[contains(@class, 'card') and contains(@class, 'h-100')]")
        self.logger.info(f"Found {len(cards)} product cards on {response.url}")

        if not cards:
            self.logger.warning("No cards found! Check XPath or page structure.")

        for card in cards:
            product = {
                "url": card.xpath(".//div[contains(@class, 'image-box')]//a/@href").get(default=""),
                "name": card.xpath(".//p[contains(@class, 'card-text')]//a/@title")
                .get(default="")
                .strip()
                .split("<br>")[0]
                .strip(),
                "price": " ".join(card.xpath(".//a[contains(@class, 'pr-text')]/text()").get(default="").split())
                .replace("Tk", "")
                .replace("(Estimated)", "")
                .strip(),
                "image": card.xpath(".//div[contains(@class, 'image-box')]//img/@src").get(default=""),
            }

            self.logger.debug(f"Extracted product: {product}")

            # Check for missing data
            if not product["url"]:
                self.logger.warning(f"Missing URL in card: {card.extract()[:200]}")
            if not product["name"]:
                self.logger.warning(f"Missing name in card: {card.extract()[:200]}")
            if not product.get("price"):
                self.logger.warning(f"Missing price in card: {card.extract()[:200]}")

            self.logger.debug(f"Extracted product: {product}")
            yield product

        # Extract pagination links for debugging
        pagination_links = response.xpath("//a[contains(@href, 'limit=100&page=')]/@href").getall()
        self.logger.debug(f"Pagination links found: {pagination_links}")
