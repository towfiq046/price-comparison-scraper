import scrapy
import json  # For reading category file
import logging
from pathlib import Path
from scrapy.loader import ItemLoader

from ..items import StartechProductDetailItem, clean_text


class StartechProductDetailsSpider(scrapy.Spider):
    """
    Spider to scrape detailed product information from Startech (startech.com.bd).
    Reads category URLs from 'output/startech_categories.jl', finds product links,
    and scrapes detail pages.
    """

    name = "startech_product_details"
    allowed_domains = ["startech.com.bd"]
    category_file = Path(__file__).resolve().parents[2] / "output/startech_categories.jl"

    def __init__(self, *args, **kwargs):
        """Initialize spider state."""
        super().__init__(*args, **kwargs)
        # No counter needed if using CLOSESPIDER_ITEMCOUNT setting

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        """Factory method: Creates spider instance."""
        spider = super(StartechProductDetailsSpider, cls).from_crawler(crawler, *args, **kwargs)
        # Log if item limit setting is active
        item_limit = crawler.settings.getint("CLOSESPIDER_ITEMCOUNT", 0)
        if item_limit > 0:
            spider.logger.info(
                f"Development limit active via CLOSESPIDER_ITEMCOUNT={item_limit}. "
                f"Spider will stop after scraping this many items."
            )
        return spider

    def start_requests(self):
        """Reads Startech category URLs from file and yields initial requests."""
        if not self.category_file.is_file():
            self.logger.error(f"Startech category file not found: {self.category_file}")
            return  # Stop spider if input file is missing

        self.logger.info(f"Reading Startech categories from: {self.category_file}")
        processed_urls = set()  # Optional: track if category file has duplicates

        try:
            with open(self.category_file, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        cat_data = json.loads(line.strip())
                        cat_url = cat_data.get("category_url")
                        # Get category name, provide default if missing
                        cat_name = cat_data.get("category_name", f"Unknown Category Line {line_num}")

                        # Basic validation
                        if not cat_url or not isinstance(cat_url, str) or self.allowed_domains[0] not in cat_url:
                            self.logger.warning(f"Skipping invalid category entry on line {line_num}: {line.strip()}")
                            continue

                        # Optional: Skip duplicate URLs from file if necessary
                        if cat_url in processed_urls:
                            continue
                        processed_urls.add(cat_url)

                        self.logger.debug(f"Yielding category request for: {cat_name} - {cat_url}")
                        yield scrapy.Request(
                            url=cat_url,
                            callback=self.parse_category,
                            errback=self.handle_error,
                            meta={"category_name": cat_name},  # Pass name for context
                        )

                    except json.JSONDecodeError:
                        self.logger.error(f"Failed to decode JSON on line {line_num}: {line.strip()}")
                    except Exception as e:
                        self.logger.error(
                            f"Error processing category line {line_num} ('{line.strip()}'): {e}", exc_info=True
                        )

        except FileNotFoundError:
            self.logger.error(f"Category file not found during open: {self.category_file}")
        except Exception as e:
            self.logger.error(f"Failed to read category file {self.category_file}: {e}", exc_info=True)

    def parse_category(self, response):
        """
        Parses a Startech category page, extracts product links, yields requests
        for product detail pages, and handles pagination.
        """
        category_name = response.meta.get("category_name", "Unknown Category")
        self.logger.info(f"Scanning Startech category: '{category_name}' from {response.url}")

        # --- Extract Product Links ---
        # Selector for the product link within each item block
        product_link_selector = "div.p-item div.p-item-details h4.p-item-name a::attr(href)"
        product_links = response.css(product_link_selector).getall()

        if not product_links:
            self.logger.warning(f"No product links found on Startech category page {response.url}")

        for product_link in product_links:
            # No item limit check needed here - handled by CLOSESPIDER_ITEMCOUNT
            absolute_product_url = response.urljoin(product_link)
            self.logger.debug(f"Yielding Startech product request for: {absolute_product_url}")
            yield scrapy.Request(
                url=absolute_product_url,
                callback=self.parse_product_detail,
                errback=self.handle_error,
                meta={"category_name": category_name},  # Pass context
            )

        # --- Handle Pagination ---
        # Selector for the "NEXT" link
        next_page_selector = 'ul.pagination li a:contains("NEXT")::attr(href)'
        # Alternative: ul.pagination li:last-child a::attr(href) - check if reliable
        next_page_url = response.css(next_page_selector).get()

        if next_page_url:
            self.logger.debug(f"Following Startech pagination link: {next_page_url}")
            yield response.follow(
                next_page_url,
                callback=self.parse_category,  # Loop back to parse next category page
                errback=self.handle_error,
                meta=response.meta,  # Carry meta info forward
            )
        else:
            self.logger.info(f"No 'NEXT' page link found for Startech category '{category_name}' on {response.url}")

    def parse_product_detail(self, response):
        """
        Parses the detailed information from a single Startech product page.
        (Code from previous step - no changes needed here for now)
        """
        self.logger.info(f"Parsing Startech product details from: {response.url}")
        category_name = response.meta.get("category_name", "Unknown Category")

        loader = ItemLoader(item=StartechProductDetailItem(), response=response)

        # --- Populate Loader using Startech selectors ---
        loader.add_css("name", "h1.product-name::text")
        loader.add_value("url", response.url)
        loader.add_value("category", category_name)
        # 1. First try to get the price from the main price element
        loader.add_css("price", "td.product-price::text")
        # 2. If price not found then try to get it from ins element
        loader.add_css("price", "td.product-price ins::text")
        loader.add_css("regular_price", "td.product-regular-price::text")
        loader.add_css("product_code", "td.product-code::text")
        loader.add_css("brand", "td.product-brand::text")
        loader.add_css("availability", "td.product-status::text")
        loader.add_css("key_features", "div.short-description ul li:not(.view-more)::text")
        loader.add_css("image_urls", 'meta[itemprop="image"]::attr(content)')

        # --- Extract Description HTML ---
        description_html_content = response.css("section#description div.full-description").get()
        if description_html_content:
            loader.add_value("description_html", description_html_content)
        else:
            self.logger.debug(
                f"No description section ('section#description div.full-description') found on {response.url}"
            )
        # --- END Description Extraction ---

        # --- Parse Specifications Table ---
        specs = {}
        current_section = "General"  # Default section
        spec_table_rows = response.css("section#specification table.data-table > *")
        for element in spec_table_rows:
            is_heading = element.xpath("self::thead").get() is not None
            if is_heading:
                heading_text = element.css("td.heading-row::text").get()
                if heading_text:
                    current_section = clean_text(heading_text)
                    if current_section not in specs:
                        specs[current_section] = {}
            else:  # tbody
                data_rows = element.css("tr")
                for row in data_rows:
                    key_elem = row.css("td.name::text").get()
                    value_elems = row.css("td.value ::text").getall()
                    key = clean_text(key_elem) if key_elem else None
                    value = clean_text(" ".join(value_elems).strip()) if value_elems else None
                    if key and value:
                        if current_section not in specs:
                            specs[current_section] = {}
                        specs[current_section][key] = value

        if specs:
            loader.add_value("specifications", specs)
        else:
            self.logger.warning(f"No specifications dictionary extracted from {response.url}")

        # Yield item - Scrapy handles item count for CLOSESPIDER_ITEMCOUNT
        yield loader.load_item()

    def handle_error(self, failure):
        """Handles errors during request processing."""
        self.logger.error(
            f"Request failed for {failure.request.url} (meta: {failure.request.meta}): {failure.value}", exc_info=True
        )
