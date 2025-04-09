import scrapy
import json
import logging
from pathlib import Path
from scrapy.loader import ItemLoader

from ..items import RyansProductDetailItem, clean_text  # Import only necessary functions


class RyansProductDetailsSpider(scrapy.Spider):
    """
    Spider to scrape detailed product information from Ryans Computers (ryans.com).
    Relies on the CLOSESPIDER_ITEMCOUNT setting for item limiting during development.
    """

    name = "ryans_product_details"
    allowed_domains = ["ryans.com"]
    category_file = Path(__file__).resolve().parents[2] / "output/ryans_categories.jl"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(RyansProductDetailsSpider, cls).from_crawler(crawler, *args, **kwargs)
        # Optional: Log if the setting is active
        item_limit = crawler.settings.getint("CLOSESPIDER_ITEMCOUNT", 0)
        if item_limit > 0:
            spider.logger.info(
                f"Development limit active via CLOSESPIDER_ITEMCOUNT={item_limit}. "
                f"Spider will stop after scraping this many items."
            )
        return spider

    def start_requests(self):
        """Reads category URLs from file and yields initial requests."""
        if not self.category_file.is_file():
            self.logger.error(f"Category file not found: {self.category_file}")
            return

        self.logger.info(f"Reading categories from: {self.category_file}")
        processed_urls = set()

        try:
            with open(self.category_file, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        cat_data = json.loads(line.strip())
                        cat_url = cat_data.get("category_url")
                        cat_name = cat_data.get("category_name", f"Unknown Category Line {line_num}")

                        if (
                            not cat_url
                            or not isinstance(cat_url, str)
                            or not cat_url.startswith("https://www.ryans.com/category/")
                        ):
                            self.logger.warning(f"Skipping invalid category entry on line {line_num}: {line.strip()}")
                            continue

                        if cat_url not in processed_urls:
                            processed_urls.add(cat_url)
                            self.logger.debug(f"Yielding category request for: {cat_name} - {cat_url}")
                            yield scrapy.Request(
                                url=cat_url,
                                callback=self.parse_category,
                                errback=self.handle_error,
                                meta={"category_name": cat_name},
                            )
                    # (Keep error handling for file reading)
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
        Parses a category page, extracts product links, and yields requests.
        Handles pagination. No item limit checks needed here.
        """
        category_name = response.meta.get("category_name", "Unknown Category")
        self.logger.info(f"Scanning category: '{category_name}' from {response.url}")

        product_links = response.css("div.card.h-100 p.list-view-text a::attr(href)").getall()
        if not product_links:
            self.logger.warning(f"No product links found on category page {response.url}")

        for product_link in product_links:
            # No limit check needed
            absolute_product_url = response.urljoin(product_link)
            self.logger.debug(f"Yielding product request for: {absolute_product_url}")
            yield scrapy.Request(
                url=absolute_product_url,
                callback=self.parse_product_detail,
                errback=self.handle_error,
                meta={"category_name": category_name},
            )

        # --- Handle Pagination ---
        next_page = response.css('ul.pagination li.page-item a[rel="next"]::attr(href)').get()
        # No limit check needed
        if next_page:
            self.logger.debug(f"Following pagination link: {next_page}")
            yield response.follow(
                next_page, callback=self.parse_category, errback=self.handle_error, meta=response.meta
            )
        else:
            self.logger.info(f"No next page found for category '{category_name}' on {response.url}")

    def parse_product_detail(self, response):
        """
        Parses the detailed information from a single product page.
        Populates and yields a RyansProductDetailItem. Scrapy handles item counting.
        """
        # No limit check needed here
        self.logger.info(f"Parsing product details from: {response.url}")
        category_name = response.meta.get("category_name", "Unknown Category")

        loader = ItemLoader(item=RyansProductDetailItem(), response=response)

        # --- Populate Loader (Selectors remain the same) ---
        loader.add_css("name", 'h1[itemprop="name"]::text')
        loader.add_value("url", response.url)
        loader.add_value("category", category_name)
        loader.add_css("price", 'meta[itemprop="price"]::attr(content)')
        loader.add_css("regular_price", "div.new-reg-price-block span.new-reg-text::text")
        loader.add_css("brand", 'div[itemprop="brand"] span[itemprop="name"]::text')
        loader.add_css("sku", 'meta[itemprop="sku"]::attr(content)')

        # Availability (Simplified logic remains)
        out_of_stock_text = response.css('div.price-block span.stock-text:contains("Out Of Stock")').get()
        if out_of_stock_text:
            loader.add_value("availability", "Out of Stock")
        else:
            loader.add_value("availability", "In Stock")

        loader.add_css("key_features", "div.overview ul.category-info li.context::text")
        loader.add_css("image_urls", "div#slideshow-items-container img.slideshow-items::attr(src)")

        # Specifications (Parsing remains the same)
        specs = {}
        spec_rows = response.css("div#add-spec-div div.row.table-hr-remove")
        if not spec_rows:
            spec_rows = response.css("div#basic-spec-div div.row.table-hr-remove")
        for row in spec_rows:
            key_list = row.css("span.att-title::text").getall()
            value_list = row.css("span.att-value::text").getall()
            key = clean_text(" ".join(key_list)) if key_list else None
            value = clean_text(" ".join(value_list)) if value_list else None
            if key and value:
                specs[key] = value
        if specs:
            loader.add_value("specifications", specs)
        else:
            self.logger.warning(f"No specifications dictionary extracted from {response.url}")

        # --- Yield Item (No counter or limit check needed here) ---
        yield loader.load_item()
        # Scrapy's CloseSpider extension will handle stopping the spider

    def handle_error(self, failure):
        """Logs errors during request processing."""
        self.logger.error(
            f"Request failed for {failure.request.url} (meta: {failure.request.meta}): {failure.value}", exc_info=True
        )
