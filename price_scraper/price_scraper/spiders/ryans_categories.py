import logging
from urllib.parse import urlparse

import scrapy
from itemadapter import ItemAdapter
from scrapy.loader import ItemLoader

from ..items import CategoryItem


class RyansCategoriesSpider(scrapy.Spider):
    """
    Extracts category and brand names/URLs from the main navigation menu
    of ryans.com. Designed to generate input for product scraping spiders.
    Outputs data to a fixed JSON Lines file defined in settings.
    """

    name = "ryans_categories"
    allowed_domains = ["ryans.com"]
    start_urls = ["https://www.ryans.com/"]
    ignored_paths = {"/", ""}

    custom_settings = {
        "FEEDS": {
            "output/ryans_categories.jl": {
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
        Parses the homepage response, extracts category links using precise
        selectors, filters them, and yields CategoryItem objects.
        """
        self.logger.info(f"Starting category extraction from {response.url}")

        category_links_selector = (
            "nav#navbar_main div.col-megamenu a[href], "
            "nav#navbar_main ul.dropdown-menu2 a[href], "
            "nav#navbar_main li.hover_drop_down > a.dropdown-toggle[href]"
        )

        seen_urls = set()

        link_selectors = response.css(category_links_selector)
        self.logger.info(f"Found {len(link_selectors)} potential category link elements.")

        for link_selector in link_selectors:
            loader = ItemLoader(item=CategoryItem(), selector=link_selector, response=response)
            relative_url = link_selector.css("::attr(href)").get()

            if not relative_url or relative_url.strip() == "#":
                continue

            absolute_url = response.urljoin(relative_url)
            parsed_url = urlparse(absolute_url)

            if absolute_url in seen_urls or parsed_url.path in self.ignored_paths or absolute_url == response.url:
                continue

            loader.add_css("category_name", "::text")
            loader.add_value("category_url", absolute_url)

            item = loader.load_item()

            adapter = ItemAdapter(item)
            if adapter.get("category_name") and adapter.get("category_url"):
                seen_urls.add(absolute_url)
                self.logger.debug(f"Yielding Category: '{adapter['category_name']}' -> {adapter['category_url']}")
                yield item
            else:
                self.logger.debug(
                    f"Item dropped post-processing (missing name/url): "
                    f"URL='{absolute_url}', Raw Name='{link_selector.css('::text').get()}'"
                )

        self.logger.info(f"Finished category extraction. Yielded {len(seen_urls)} unique category items.")

    def handle_error(self, failure):
        """Handles errors during the initial request."""
        self.logger.error(f"Request failed for {failure.request.url}: {failure.value}", exc_info=True)
