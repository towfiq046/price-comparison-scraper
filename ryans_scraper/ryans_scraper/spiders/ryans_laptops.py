import logging
from scrapy.linkextractors import LinkExtractor
from scrapy.selector import Selector
from scrapy.spiders import CrawlSpider, Rule


class RyansLaptopsSpider(CrawlSpider):
    name = "ryans_laptops"
    allowed_domains = ["ryans.com"]
    start_urls = ["https://www.ryans.com/category/laptop-all-laptop?limit=100"]

    rules = (
        Rule(LinkExtractor(allow=r"https://www.ryans.com/[^/]+-laptop$"), callback="parse_product", follow=False),
        Rule(LinkExtractor(allow=r"limit=100&page=\d+"), callback="parse_category", follow=True),
    )
    def parse_category(self, response):
        self.logger.info(f"Parsing category page: {response.url}")
        cards = response.xpath("//div[contains(@class, 'card') and contains(@class, 'h-100')]")
        self.logger.info(f"Found {len(cards)} product containers")
        for card in cards[:5]:
            link = card.xpath(".//div[contains(@class, 'image-box')]//a/@href").get()
            name = card.xpath(".//p[contains(@class, 'card-text')]//a/text()").get(default="").strip()
            self.logger.info(f"Product: Name: {name}, Link: {link}")

    def parse_product(self, response):
        product = {
            "url": response.url,
            "name": self._extract_name(response),
            "product_id": self._extract_product_id(response),
            "price": self._extract_price(response),
            "discount": self._extract_discount(response),
            "specifications": self._extract_specifications(response),
            "emi_summary": self._extract_emi_summary(response),
            "emi_plans": [],
            "note": "",
            "offers": self._extract_offers(response),
            "image": self._extract_image(response),
            "out_of_stock": False,  # Default to False
        }
        self._extract_emi_tooltip(response, product)
        # breakpoint()

        # Check stock status
        stock_status = response.xpath("//span[contains(text(), 'Out Of Stock')]").get()
        if stock_status or (not product["price"] and not product["emi_plans"]):
            product["out_of_stock"] = True
            self.logger.info(f"Product marked as out of stock: {response.url}")

        # Log missing data
        if not product["price"] and not product["out_of_stock"]:
            self.logger.warning(f"No price found for in-stock product: {response.url}")
        if not product["emi_plans"] and not product["out_of_stock"]:
            self.logger.warning(f"No EMI plans found for in-stock product: {response.url}")

        yield product

    def _extract_name(self, response):
        name = response.css('h1[itemprop="name"]::text').get(default="").strip()
        if not name:
            name = (
                response.css("title::text")
                .get(default="")
                .replace(" Price in Bangladesh", "")
                .replace(" | RYANS", "")
                .strip()
            )
        return name

    def _extract_product_id(self, response):
        return response.xpath('//p[contains(text(), "Product Id:")]/span/text()').get(default="").strip()

    def _extract_price(self, response):
        price = (
            response.css("span.new-sp-text::text").get(default="").strip()
            or response.css("span.price::text").get(default="").strip()
            or response.xpath("//span[contains(@class, 'price')]//text()").get(default="").strip()
        )
        return price

    def _extract_discount(self, response):
        return response.css("span.fs-text2::text").get(default="").strip()

    def _extract_specifications(self, response):
        specs = {}
        for item in response.css("ul.category-info li"):
            text = item.css("::text").get()
            if text and " - " in text:
                key, value = text.split(" - ", 1)
                specs[key.strip()] = value.strip()
        return specs

    def _extract_emi_summary(self, response):
        return response.xpath("//div[@class='emi-cbox-text']/text()").get(default="").strip()

    def _extract_emi_tooltip(self, response, product):
        tooltip_elements = response.css('[data-bs-toggle="tooltip"]')
        if not tooltip_elements:
            self.logger.debug(f"No EMI tooltip elements found on {response.url}")
        for element in tooltip_elements:
            tooltip_html = element.attrib.get("data-bs-original-title", "") or element.attrib.get("title", "")
            button_text = (
                element.css("::text").get(default="").strip()
                or element.css("span::text").get(default="").strip()
                or element.xpath("string(.)").get(default="").strip()
            )
            if tooltip_html and ("EMI" in tooltip_html or "months" in tooltip_html):
                tooltip_selector = Selector(text=tooltip_html)
                emi_plans = tooltip_selector.css("table tbody tr td::text").getall()
                note = tooltip_selector.css("span.emi-note-st::text").get(default="")
                if "EMI TK" in button_text:
                    product["emi_plans"] = [plan.strip() for plan in emi_plans if "BDT" in plan and "for" in plan]
                    product["note"] = note
                self.logger.debug(f"EMI found: button_text={button_text}, plans={emi_plans}, note={note}")

    def _extract_offers(self, response):
        offer_links = response.css("div.offers a::attr(href)").getall()
        return [link.split("/")[-1].replace("-", " ").title() for link in offer_links if "offers" in link]

    def _extract_image(self, response):
        return response.css("img.slideshow-items.active::attr(src)").get(default="") or response.css(
            'meta[itemprop="image"]::attr(content)'
        ).get(default="")
