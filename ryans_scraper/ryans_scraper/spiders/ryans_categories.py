import scrapy
from urllib.parse import urlparse


class RyansCategoriesSpider(scrapy.Spider):
    """
    A simple spider to extract the main category names and URLs
    from the primary navigation menu of ryans.com.

    This spider is intended for reconnaissance to understand the site structure
    before building specific product scrapers. It does not follow links or
    scrape product details.

    Outputs a list of dictionaries: {'category_name': 'Name', 'category_url': 'URL'}
    """

    name = "ryans_categories"
    allowed_domains = ["ryans.com", "www.ryans.com"]  # Added www just in case, though OffsiteMiddleware handles it
    start_urls = ["https://www.ryans.com/"]

    # Define a set of base URLs or paths to ignore if needed
    # For now, just ignoring the root path ('/') and the full start URL
    ignored_paths = {"/", ""}  # Add more if needed, e.g., '/login'

    def parse(self, response):
        """
        Parses the homepage response to extract category links from the main navigation.
        """
        self.logger.info(f"Starting category extraction from {response.url}")

        # Selector targets all links with an href inside the main navbar
        category_links = response.css("nav#navbar_main a[href]")

        seen_urls = set()  # Keep track of URLs we've already yielded

        for link in category_links:
            relative_url = link.css("::attr(href)").get()
            category_name = link.css("::text").get()

            # Basic cleaning and validation
            if not relative_url or not category_name:
                continue  # Skip if no URL or name

            category_name = category_name.strip()
            if not category_name:
                continue  # Skip if name is only whitespace

            # Ignore placeholder links
            if relative_url.strip() == "#":
                continue

            # Create absolute URL
            absolute_url = response.urljoin(relative_url)

            # Parse the URL to easily check the path
            parsed_url = urlparse(absolute_url)

            # Ignore the home link or links matching ignored paths
            if parsed_url.path in self.ignored_paths or absolute_url == response.url:
                continue

            # Avoid yielding duplicate URLs
            if absolute_url in seen_urls:
                continue
            seen_urls.add(absolute_url)

            # Log the found category (optional, can be noisy)
            # self.logger.info(f"Found Category: '{category_name}' -> {absolute_url}")

            yield {
                "category_name": category_name.replace("\n", "").replace("\t", "").strip(),  # Added extra cleaning
                "category_url": absolute_url,
            }

        self.logger.info(f"Finished category extraction. Found {len(seen_urls)} unique category links.")
