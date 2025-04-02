import json
import os
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
        self.seen_urls = set()

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_item(self, item, spider):
        """
        Process an item by checking the URL, verifying duplicate entries
        and validating price information.
        """
        adapter = ItemAdapter(item)
        url = adapter.get("url")

        if not url:
            raise DropItem(f"Missing URL in item: {item}")

        self._check_duplicate(url)
        self.seen_urls.add(url)
        self._validate_price(adapter, url)

        return item

    def _check_duplicate(self, url):
        """Check if the URL is already processed and raise DropItem if found."""
        if url in self.seen_urls:
            self.logger.debug(f"Duplicate item dropped: {url}")
            raise DropItem(f"Duplicate item found: {url}")

    def _validate_price(self, adapter, url):
        """Validate the price field (assumes cleaning done by ItemLoader)."""
        price_str = adapter.get("price")
        if price_str:
            try:
                adapter["price"] = float(price_str)
            except ValueError:
                original_price_before_validation = adapter.item.get("price", "N/A")
                self.logger.warning(
                    f"Invalid price format '{original_price_before_validation}' for url '{url}'. Setting to None."
                )
                adapter["price"] = None
        else:
            # Price was missing or became empty after cleaning
            self.logger.warning(f"Missing or empty price after cleaning for url '{url}'")
            # Ensure it's None if it was an empty string
            adapter["price"] = None


class JsonLinesExportPipeline:
    """
    Pipeline to export collected items incrementally to a JSON Lines file.
    Each responsibility (directory management, file handling, serialization, writing)
    is handled more distinctly.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.file_handle = None  # File handle for writing
        self.filename = None  # Store filename for logging clarity

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def open_spider(self, spider):
        """
        Called when the spider starts.
        Generates filename, ensures directory exists, and opens the file handle.
        """
        self.filename = self._generate_filename()
        output_dir = os.path.dirname(self.filename)

        if not self._ensure_output_directory_exists(output_dir):
            self.logger.error("Export directory could not be created or verified. Pipeline will not write.")
            return

        try:
            self.file_handle = open(self.filename, "w", encoding="utf-8")
            self.logger.info(f"JSON Lines export pipeline started. Writing to: {self.filename}")
        except OSError as e:
            self.logger.error(f"Could not open file {self.filename} for writing. Error: {e}")
            self.file_handle = None

    def process_item(self, item, spider):
        """
        Processes an item: serializes it and writes the resulting line to the file.
        Checks if the pipeline is in a valid state to write.
        """
        if not self.file_handle:
            self.logger.warning(
                f"Export file '{self.filename}' not open. Skipping item: {ItemAdapter(item).get('url', 'N/A')}"
            )
            return item  # Allow item to pass to other pipelines if any

        json_string = self._serialize_item(item)

        if json_string is not None:
            self._write_line(json_string)

        return item  # Always return item for pipeline chain

    def close_spider(self, spider):
        """
        Called when the spider is closed; closes the export file handle.
        """
        if self.file_handle:
            self.file_handle.close()
            self.logger.info(f"JSON Lines export pipeline finished. File '{self.filename}' closed.")
        elif self.filename:
            self.logger.warning(f"JSON Lines export file '{self.filename}' was not open during close_spider.")

    def _generate_filename(self):
        """Generates a unique, timestamped filename for the export."""
        output_dir = "output"
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return os.path.join(output_dir, f"export_{timestamp}.jsonl")

    def _ensure_output_directory_exists(self, directory_path):
        """Checks if the output directory exists and creates it if necessary."""
        if directory_path and not os.path.exists(directory_path):
            try:
                os.makedirs(directory_path)
                self.logger.info(f"Created output directory: {directory_path}")
                return True
            except OSError as e:
                self.logger.error(f"Could not create output directory {directory_path}. Error: {e}")
                return False
        return True

    def _serialize_item(self, item):
        """Serializes a single Scrapy item to a JSON string."""
        try:
            # Adapting and dumping are part of the serialization responsibility
            return json.dumps(ItemAdapter(item).asdict())
        except TypeError as e:
            self.logger.error(f"Failed to serialize item to JSON: {e}. Item: {item}")
            return None  # Indicate serialization failure

    def _write_line(self, line):
        """Writes a single line string (already serialized) to the file."""
        try:
            self.file_handle.write(line + "\n")
        except OSError as e:
            self.logger.error(f"Failed to write line to file {self.filename}: {e}. Line: {line[:100]}...")
