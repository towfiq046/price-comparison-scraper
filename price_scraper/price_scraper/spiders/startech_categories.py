import logging

import scrapy
from itemadapter import ItemAdapter
from scrapy.loader import ItemLoader

from ..items import CategoryItem


class StartechCategoriesSpider(scrapy.Spider):
    """
    Extracts category and brand names/URLs from the main navigation menu
    of startech.com.bd. Outputs to a fixed JSON Lines file.
    """

    name = "startech_categories"
    allowed_domains = ["startech.com.bd"]
    start_urls = ["https://www.startech.com.bd/"]

    custom_settings = {
        "FEEDS": {
            "output/startech_categories.jl": {
                "format": "jsonlines",
                "encoding": "utf-8",
                "overwrite": True,
                "item_classes": ["price_scraper.items.CategoryItem"],
            }
        },
        "ITEM_PIPELINES": {
            "price_scraper.pipelines.JsonLinesExportPipeline": None,
            "price_scraper.pipelines.DropDuplicatesPipeline": 100,
        },
    }

    def start_requests(self):
        """Yields the initial request with error handling."""
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse, errback=self.handle_error)

    def parse(self, response):
        """
        Parses the homepage, extracts category links from the main navigation,
        filters them, and yields CategoryItem objects.
        """
        self.logger.info(f"Starting Startech category extraction from {response.url}")

        category_links_selector = "nav#main-nav ul a.nav-link[href]"
        exclude_selector = "a.see-all"

        seen_urls = set()
        link_selectors = response.css(category_links_selector).xpath(
            f"./parent::*[not(self::{exclude_selector.replace('a.', '')})]/a"
        )

        self.logger.info(f"Found {len(link_selectors)} potential category link elements using selector.")

        for link_selector in link_selectors:
            loader = ItemLoader(item=CategoryItem(), selector=link_selector, response=response)

            relative_url = link_selector.css("::attr(href)").get()
            if not relative_url or relative_url.strip() == "#":
                continue

            absolute_url = response.urljoin(relative_url)

            if absolute_url in seen_urls:
                continue

            loader.add_css("category_name", "::text")
            loader.add_value("category_url", absolute_url)

            item = loader.load_item()
            adapter = ItemAdapter(item)

            if adapter.get("category_name") and adapter.get("category_url"):
                seen_urls.add(absolute_url)
                self.logger.debug(f"Yielding Category: '{adapter['category_name']}' -> {adapter['category_url']}")
                yield item

        self.logger.info(f"Finished Startech category extraction. Yielded {len(seen_urls)} unique category items.")

    def handle_error(self, failure):
        """Handles errors during the initial request."""
        self.logger.error(f"Request failed for {failure.request.url}: {failure.value}", exc_info=True)
