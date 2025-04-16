import json
import logging
import os
from datetime import datetime

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


class DropDuplicatesPipeline:
    """Drops duplicate items seen within the same crawl run based on URL."""

    DUPLICATE_KEY_FIELD_MAP = {
        "ryans_categories": "category_url",
        "ryans_product_details": "url",
        "startech_categories": "category_url",
        "startech_product_details": "url",
    }

    def __init__(self):
        self.keys_seen = set()
        self.logger = logging.getLogger(__name__)

    def process_item(self, item, spider):
        key_field = self.DUPLICATE_KEY_FIELD_MAP.get(spider.name)
        if not key_field:
            # Default or skip check if spider not configured
            self.logger.debug(f"Duplicate key field not configured for spider '{spider.name}'. Skipping check.")
            return item

        adapter = ItemAdapter(item)
        key_value = adapter.get(key_field)

        if not key_value:
            self.logger.warning(f"Item missing duplicate key field '{key_field}'...")
            return item

        item_key_tuple = (key_field, key_value)

        if item_key_tuple in self.keys_seen:
            drop_msg = f"Duplicate item found based on field '{key_field}': {key_value}"
            self.logger.warning(f"DROP DUPLICATE: {drop_msg}")
            # --- End Log ---
            raise DropItem(drop_msg)
        else:
            self.keys_seen.add(item_key_tuple)
            return item


class RequiredFieldsPipeline:
    """
    Drops items missing essential fields. Warns about missing optional-but-important fields.
    """

    # Define strictly essential fields that MUST cause a drop if missing
    ESSENTIAL_FIELDS_MAP = {
        "ryans_product_details": ["name", "price", "url", "sku", "availability", "brand"],
        "startech_product_details": ["name", "price", "url", "availability", "product_code", "brand"],
    }
    # Define fields that are important but shouldn't cause a drop if missing
    IMPORTANT_FIELDS_MAP = {
        "ryans_product_details": ["specifications"],
        "startech_product_details": ["specifications"],
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process_item(self, item, spider):
        essential_fields = self.ESSENTIAL_FIELDS_MAP.get(spider.name, [])
        important_fields = self.IMPORTANT_FIELDS_MAP.get(spider.name, [])

        adapter = ItemAdapter(item)

        # --- Check Essential Fields ---
        missing_essential = [field for field in essential_fields if not adapter.get(field)]
        if "price" in essential_fields and (adapter.get("price") is None or adapter["price"] <= 0):
            missing_essential.append("price (invalid/missing)")

        if missing_essential:
            msg = f"DROP: Missing essential fields: {', '.join(missing_essential)} in item from spider '{spider.name}' ({adapter.get('url') or adapter.get('name', 'N/A')})"
            self.logger.warning(msg)
            raise DropItem(msg)  # Drop items missing essential data

        # --- Check Important (but not critical) Fields ---
        missing_important = []
        for field in important_fields:
            value = adapter.get(field)
            if value is None:  # Check for None explicitly
                missing_important.append(f"{field} (None)")
            # Specific check for specifications dictionary
            elif field == "specifications" and not isinstance(value, dict):
                missing_important.append(f"{field} (not dict)")
            elif field == "specifications" and not value:  # Check if dict is empty
                missing_important.append(f"{field} (empty dict)")

        if missing_important:
            # Log a warning but DO NOT drop the item
            self.logger.warning(
                f"WARN: Missing important fields: {', '.join(missing_important)} in item from spider '{spider.name}' "
                f"({adapter.get('url') or adapter.get('name', 'N/A')})"
            )
            # Ensure specifications field is None if it failed checks, helps downstream processing
            if (
                "specifications (not dict)" in missing_important
                or "specifications (empty dict)" in missing_important
                or "specifications (None)" in missing_important
            ):
                adapter["specifications"] = None

        return item  # Always return item after checks


class JsonLinesExportPipeline:
    """
    Pipeline to export collected items incrementally to a timestamped JSON Lines file.
    Handles directory creation, file opening/closing, and serialization.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.file_handle = None
        self.filename = None
        self.items_written = 0

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def open_spider(self, spider):
        self.filename = self._generate_filename(spider)
        output_dir = os.path.dirname(self.filename)
        if not self._ensure_output_directory_exists(output_dir):
            self.logger.error("Export directory could not be created/verified. Pipeline disabled.")
            return
        try:
            self.file_handle = open(self.filename, "w", encoding="utf-8")
            self.logger.info(f"JSON Lines export pipeline started. Writing to: {self.filename}")
        except OSError as e:
            self.logger.error(f"Could not open file {self.filename} for writing. Error: {e}")
            self.file_handle = None

    def process_item(self, item, spider):
        if not item or not self.file_handle:
            if not self.file_handle and self.filename:
                self.logger.warning(
                    f"Export file '{self.filename}' not open. Skipping item: {ItemAdapter(item).get('url', 'N/A') if item else 'None'}"
                )
            return item

        json_string = self._serialize_item(item)
        if json_string is None:
            return item

        if self._write_line(json_string):
            self.items_written += 1

        return item

    def close_spider(self, spider):
        if self.file_handle:
            try:
                self.file_handle.close()
                self.logger.info(
                    f"JSON Lines export pipeline finished. Wrote {self.items_written} items to '{self.filename}'."
                )
            except OSError as e:
                self.logger.error(f"Error closing file {self.filename}. Error: {e}")
        elif self.filename:
            self.logger.warning(f"JSON Lines export file '{self.filename}' was not open during close_spider.")
        self.file_handle = None
        self.filename = None
        self.items_written = 0

    def _generate_filename(self, spider):
        output_dir = "output"
        timestamp = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        return os.path.join(output_dir, f"{spider.name}_export_{timestamp}.jl")

    def _ensure_output_directory_exists(self, directory_path):
        if not directory_path:
            self.logger.error("Output directory path is invalid.")
            return False
        try:
            os.makedirs(directory_path, exist_ok=True)
            if not os.path.isdir(directory_path):
                raise OSError(f"Directory '{directory_path}' could not be confirmed after makedirs.")
            return True
        except OSError as e:
            self.logger.error(f"Could not create or verify output directory {directory_path}. Error: {e}")
            return False

    def _serialize_item(self, item):
        try:
            item_dict = ItemAdapter(item).asdict()
            return json.dumps(item_dict)
        except TypeError as e:
            self.logger.error(f"Failed to serialize item to JSON: {e}. Item: {item}")
            return None

    def _write_line(self, line):
        try:
            self.file_handle.write(line + "\n")
            return True
        except OSError as e:
            self.logger.error(f"Failed to write line to file {self.filename}: {e}. Line: {line[:100]}...")
            return False
