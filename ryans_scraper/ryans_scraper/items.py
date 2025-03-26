from scrapy import Item, Field
from itemloaders.processors import MapCompose, TakeFirst


def clean_text(value):
    """Strip whitespace from text."""
    return value.strip() if value else ""


def clean_price(value):
    """Clean price by removing 'Tk', '(Estimated)', and normalizing spaces."""
    if not value:
        return ""
    return " ".join(value.split()).replace("Tk", "").replace("(Estimated)", "").strip()


class LaptopItem(Item):
    """
    Item class for laptop data scraped from ryans.com.
    Defines fields with input/output processors for cleaning.
    """

    url = Field(input_processor=MapCompose(clean_text), output_processor=TakeFirst())
    name = Field(
        input_processor=MapCompose(clean_text, lambda x: x.split("<br>")[0]),  # Take text before <br>
        output_processor=TakeFirst(),
    )
    price = Field(input_processor=MapCompose(clean_price), output_processor=TakeFirst())
    image = Field(input_processor=MapCompose(clean_text), output_processor=TakeFirst())
