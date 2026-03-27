import scrapy


class MhnowItem(scrapy.Item):
    """
    Represents a single scraped entity from monsterhunternow.com.

    All selector-based fields are populated by mhnow_spider.py.
    Add or remove fields here as the site structure becomes clearer.
    """

    # Which category page this item came from
    # (monsters / weapons / armor / skills)
    category = scrapy.Field()

    # Canonical display name of the item
    name = scrapy.Field()

    # Full description / flavour text found on the detail page
    description = scrapy.Field()

    # List of dicts like [{"label": "Attack", "value": "350"}, ...]
    # Populated from the stats / attributes table on the detail page
    stats = scrapy.Field()

    # List of weakness entries, e.g. ["Fire", "Thunder"]
    # Only present for monster detail pages; empty list otherwise
    weaknesses = scrapy.Field()

    # Absolute URLs of all images found on the detail page.
    # Scrapy's built-in ImagesPipeline (see pipelines.py) will download
    # these automatically when enabled.
    image_urls = scrapy.Field()

    # Catch-all dict for any additional key/value pairs found on the page
    # that do not map to a dedicated field above.
    extra_fields = scrapy.Field()

    # Canonical URL of the detail page this item was scraped from
    source_url = scrapy.Field()
