import json
import logging
from datetime import datetime

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


class LaptopValidationPipeline:
    """
    Pipeline to validate and clean scraped LaptopItem data.
    Ensures price is numeric and removes duplicates by URL.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.seen_urls = set()  # Track URLs to remove duplicates

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_item(self, item, spider):
        """
        Process an item by checking for duplicates, registering its URL, and validating its price.

        Args:
            item: The scraped LaptopItem.
            spider: The spider instance processing the item.
            
        Returns:
            The processed item.
        
        Raises:
            DropItem: If a duplicate URL is detected.
        """
        adapter = ItemAdapter(item)
        url = adapter.get("url")

        self._check_duplicate(url)
        self.seen_urls.add(url)
        self._validate_price(adapter, url)

        return item

    def _check_duplicate(self, url):
        """
        Check if a URL has already been processed; drops the item if so.

        Args:
            url: The URL to check.

        Raises:
            DropItem: If the URL is already in the seen set.
        """
        if url in self.seen_urls:
            self.logger.debug(f"Duplicate item dropped: {url}")
            raise DropItem(f"Duplicate item found: {url}")

    def _validate_price(self, adapter, url):
        """
        Validate and convert the price field.

        This method removes any commas from the price string and converts it
        to a float. If the conversion fails or the price is missing, a warning is logged.

        Args:
            adapter: The ItemAdapter for the current item.
            url: The item's URL (used for logging).
        """
        price = adapter.get("price")
        if price:
            try:
                # Remove commas if any and convert to float
                adapter["price"] = float(price.replace(",", ""))
            except ValueError:
                self.logger.warning(f"Invalid price '{price}' for {url}. Setting to None.")
                adapter["price"] = None
        else:
            self.logger.warning(f"Missing price for {url}")


class JsonExportPipeline:
    """
    Pipeline to export collected items to a JSON file with a timestamp.
    It gathers all scraped items and writes them to disk when the spider closes.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.items = []

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def open_spider(self, spider):
        """
        Called when the spider starts.

        Logs that the JSON export pipeline has started.
        """
        self.logger.info("JSON export pipeline started.")

    def process_item(self, item, spider):
        """
        Collect each scraped item for later export.

        Args:
            item: The scraped item.
            spider: The spider that produced the item.

        Returns:
            The unmodified item.
        """
        self.items.append(ItemAdapter(item).asdict())
        return item

    def _generate_filename(self):
        """
        Generate a human-readable filename for the export JSON file.

        Returns:
            A string in the format 'laptops_lite_YYYY-MM-DD_HH-MM-SS.json'.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return f"laptops_lite_{timestamp}.json"

    def _write_items_to_file(self, filename):
        """
        Write the collected items to a JSON file.

        Args:
            filename: The name of the file to write.

        Side effects:
            Writes a JSON file containing all collected items.
        """
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.items, f, indent=2)
        self.logger.info(f"Saved {len(self.items)} items to {filename}")

    def close_spider(self, spider):
        """
        Called when the spider is closed; exports all collected items to a JSON file.

        Args:
            spider: The spider instance that has finished running.

        Side effects:
            - Generates a timestamped filename.
            - Writes the collected items to the file.
            - Logs the number of items saved.
        """
        filename = self._generate_filename()
        self._write_items_to_file(filename)