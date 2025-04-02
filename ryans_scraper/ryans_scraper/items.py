from scrapy import Item, Field
from itemloaders.processors import MapCompose, TakeFirst


def clean_text(value):
    """Strip whitespace from text."""
    return value.strip() if value else ""


def extract_name_before_br(text):
    """
    Extracts and returns the substring before the first '<br>' in the given text,
    or an empty string if text is falsy.
    """
    if not text:
        return ""
    return text.split("<br>")[0]


def clean_price(value):
    """Clean price by removing 'Tk', '(Estimated)', commas, and normalizing spaces."""
    if not value:
        return ""
    return " ".join(value.split()).replace("Tk", "").replace("(Estimated)", "").replace(",", "").strip()


class LaptopItem(Item):
    """
    Item class for laptop data scraped from ryans.com.
    Defines fields with input/output processors for cleaning.
    """

    url = Field(input_processor=MapCompose(clean_text), output_processor=TakeFirst())
    name = Field(
        input_processor=MapCompose(clean_text, extract_name_before_br),
        output_processor=TakeFirst(),
    )
    price = Field(input_processor=MapCompose(clean_price), output_processor=TakeFirst())
    image = Field(input_processor=MapCompose(clean_text), output_processor=TakeFirst())
