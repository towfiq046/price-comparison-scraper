import scrapy
from itemloaders.processors import TakeFirst, MapCompose, Identity
from w3lib.html import remove_tags
import re
import logging

# --- Helper Functions ---


def clean_text(text):
    """Removes leading/trailing whitespace, reduces internal whitespace, handles non-strings."""
    if text:
        return " ".join(str(text).split()).strip()
    return text


def parse_price(text):
    """Extracts numerical price, removing any non-digit/non-decimal characters."""
    if not text:
        return None
    cleaned_text = re.sub(r"[^\d.]", "", str(text))
    try:
        if not cleaned_text or cleaned_text.count(".") > 1:
            logging.debug(f"Price parsing resulted in invalid format: '{cleaned_text}' from '{text}'")
            return None
        price = float(cleaned_text)
        # Treat 0 price as potentially unavailable or 'Call for Price'
        return price if price > 0 else None
    except (ValueError, TypeError) as e:
        logging.warning(f"Could not parse price from text: '{text}' -> cleaned: '{cleaned_text}'. Error: {e}")
        return None


# --- Item Definition for Category Links ---


class CategoryItem(scrapy.Item):
    """Represents a category link extracted from the navigation menu."""

    category_name = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )
    category_url = scrapy.Field(output_processor=TakeFirst())


# --- Item Definition for Product Detail Page ---


class RyansProductDetailItem(scrapy.Item):
    """Represents a product detail page with all relevant information."""

    # --- Core Product Info ---
    name = scrapy.Field(
        input_processor=MapCompose(remove_tags, clean_text),
        output_processor=TakeFirst(),
    )
    url = scrapy.Field(output_processor=TakeFirst())
    category = scrapy.Field(input_processor=MapCompose(clean_text), output_processor=TakeFirst())
    brand = scrapy.Field(input_processor=MapCompose(clean_text), output_processor=TakeFirst())
    sku = scrapy.Field(input_processor=MapCompose(clean_text), output_processor=TakeFirst())

    # --- Pricing Info ---
    price = scrapy.Field(
        input_processor=MapCompose(parse_price),
        output_processor=TakeFirst(),
    )
    regular_price = scrapy.Field(
        input_processor=MapCompose(parse_price),
        output_processor=TakeFirst(),
    )

    # --- Availability Info ---
    availability = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst(),
    )

    # --- Features/Specifications ---
    specifications = scrapy.Field(output_processor=TakeFirst())
    key_features = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=Identity(),
    )

    # --- Media ---
    image_urls = scrapy.Field(
        input_processor=MapCompose(str.strip),
        output_processor=Identity(),
    )
    images = scrapy.Field()


class StartechProductDetailItem(scrapy.Item):
    """
    Represents detailed product information scraped from startech.com.bd.
    """

    # --- Core Product Info ---
    name = scrapy.Field(input_processor=MapCompose(remove_tags, clean_text), output_processor=TakeFirst())
    url = scrapy.Field(output_processor=TakeFirst())
    category = scrapy.Field(
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )
    brand = scrapy.Field(input_processor=MapCompose(clean_text), output_processor=TakeFirst())
    product_code = scrapy.Field(  # Startech uses 'Product Code'
        input_processor=MapCompose(clean_text), output_processor=TakeFirst()
    )

    # --- Pricing Info ---
    price = scrapy.Field(
        input_processor=MapCompose(parse_price),
        output_processor=TakeFirst(),
    )
    regular_price = scrapy.Field(
        input_processor=MapCompose(parse_price),
        output_processor=TakeFirst(),
    )

    # --- Availability Info ---
    availability = scrapy.Field(input_processor=MapCompose(clean_text), output_processor=TakeFirst())

    # --- Features/Specifications ---
    specifications = scrapy.Field(
        output_processor=TakeFirst()
    )
    key_features = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=Identity(),
    )

    # --- Media ---
    image_urls = scrapy.Field(
        input_processor=MapCompose(str.strip),
        output_processor=Identity(),
    )
    images = scrapy.Field()
