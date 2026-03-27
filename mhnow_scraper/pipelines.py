import json
import logging
from itemadapter import ItemAdapter

_log = logging.getLogger(__name__)


# Categories that are always present in mhnow.json even when empty.
# Keep this list in sync with CATEGORY_URLS in mhnow_spider.py.
_KNOWN_CATEGORIES = ["monsters", "weapons", "armor", "skills"]


class GroupedOutputPipeline:
    """
    Writes mhnow.json grouped by category::

        {
          "monsters": [...],
          "weapons":  [...],
          "armor":    [...],
          "skills":   [...]
        }

    All four category keys are always present, even when empty.
    This pipeline writes the file in close_spider() so it replaces
    Scrapy's built-in FEEDS flat-array exporter.
    """

    output_file = "mhnow.json"

    def open_spider(self):
        # Pre-populate known categories so they always appear in output.
        self.grouped: dict = {cat: [] for cat in _KNOWN_CATEGORIES}

    def process_item(self, item):
        adapter = ItemAdapter(item)
        category = adapter.get("category") or "unknown"
        if category not in self.grouped:
            self.grouped[category] = []
        self.grouped[category].append(dict(item))
        return item

    def close_spider(self):
        with open(self.output_file, "w", encoding="utf-8") as fh:
            json.dump(self.grouped, fh, indent=2, ensure_ascii=False)
        _log.info("Grouped output written to %s", self.output_file)


class MhnowPipeline:
    """
    Default pass-through pipeline.

    Add any normalisation / validation logic here.
    For example: strip whitespace from text fields, ensure image_urls is
    always a list, etc.
    """

    def process_item(self, item):
        adapter = ItemAdapter(item)

        # Normalise text fields: strip leading/trailing whitespace
        for field in ("name", "description", "category"):
            if adapter.get(field):
                adapter[field] = adapter[field].strip()

        # Ensure list fields are always lists (never None)
        for field in ("stats", "weaknesses", "image_urls"):
            if adapter.get(field) is None:
                adapter[field] = []

        # Ensure extra_fields is always a dict
        if adapter.get("extra_fields") is None:
            adapter["extra_fields"] = {}

        return item


# ---------------------------------------------------------------------------
# Optional: Scrapy built-in image downloader pipeline
# ---------------------------------------------------------------------------
# Uncomment the class below and update settings.py to activate it:
#
#   ITEM_PIPELINES = {
#       "mhnow_scraper.pipelines.MhnowPipeline": 300,
#       "mhnow_scraper.pipelines.MhnowImagesPipeline": 400,
#   }
#   IMAGES_STORE = "images"
#
# You also need `Pillow` installed (already listed in requirements.txt).
# ---------------------------------------------------------------------------

# from scrapy.pipelines.images import ImagesPipeline
# from scrapy import Request
#
# class MhnowImagesPipeline(ImagesPipeline):
#     """Download images listed in item['image_urls'] to IMAGES_STORE."""
#
#     def get_media_requests(self, item, info):
#         for url in item.get("image_urls", []):
#             yield Request(url)
#
#     def file_path(self, request, response=None, info=None, *, item=None):
#         category = item.get("category", "misc") if item else "misc"
#         filename = request.url.split("/")[-1]
#         return f"{category}/{filename}"
