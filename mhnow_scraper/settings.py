# ============================================================
# Monster Hunter Now Scraper — Scrapy Settings
# ============================================================

BOT_NAME = "mhnow_scraper"

SPIDER_MODULES = ["mhnow_scraper.spiders"]
NEWSPIDER_MODULE = "mhnow_scraper.spiders"

# ------------------------------------------------------------------
# Politeness / identity
# ------------------------------------------------------------------

# Obey robots.txt rules.  Set to False only if you have confirmed the
# target site allows scraping for personal/research use.
ROBOTSTXT_OBEY = True

# A realistic browser User-Agent so the server does not immediately
# reject the requests as a generic bot.
DEFAULT_REQUEST_HEADERS = {
    "Accept":
        "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
}

# Base delay between requests (seconds).
# Applies before AutoThrottle takes effect.
DOWNLOAD_DELAY = 2

# Randomise delay between 0.5× and 1.5× DOWNLOAD_DELAY to look more
# human and avoid triggering rate-limiters.
RANDOMIZE_DOWNLOAD_DELAY = True

# Only allow one concurrent request per domain to be extra polite.
CONCURRENT_REQUESTS_PER_DOMAIN = 1

# ------------------------------------------------------------------
# AutoThrottle — dynamically adjusts delays based on server latency
# ------------------------------------------------------------------
AUTOTHROTTLE_ENABLED = True

# Starting delay (seconds); AutoThrottle will tune this up/down.
AUTOTHROTTLE_START_DELAY = 2

# Upper bound for the delay AutoThrottle can set (seconds).
AUTOTHROTTLE_MAX_DELAY = 20

# Target concurrency: number of parallel requests AutoThrottle aims
# to keep in-flight at once.
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# Log AutoThrottle decisions to the console for visibility.
AUTOTHROTTLE_DEBUG = False

# ------------------------------------------------------------------
# Retry middleware
# ------------------------------------------------------------------
RETRY_ENABLED = True

# Number of times Scrapy will retry a failed request.
RETRY_TIMES = 3

# HTTP status codes that trigger a retry.
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# ------------------------------------------------------------------
# Item pipelines
# ------------------------------------------------------------------
ITEM_PIPELINES = {
    # MhnowPipeline normalises fields first (lower number = higher priority)
    "mhnow_scraper.pipelines.MhnowPipeline": 300,
    # GroupedOutputPipeline writes mhnow.json grouped by category.
    # It always emits all four category keys even when no items are scraped.
    "mhnow_scraper.pipelines.GroupedOutputPipeline": 500,
    # Uncomment the line below and set IMAGES_STORE to enable image
    # downloading via Scrapy's built-in ImagesPipeline.
    # "mhnow_scraper.pipelines.MhnowImagesPipeline": 400,
}

# ------------------------------------------------------------------
# Feed export
# ------------------------------------------------------------------
# Scrapy's built-in FEEDS exporter is intentionally disabled here.
# GroupedOutputPipeline (above) writes mhnow.json instead, producing
# a dict keyed by category so all four keys are always present:
#
#   { "monsters": [...], "weapons": [...], "armor": [...], "skills": [...] }
#
# Run:  scrapy crawl mhnow
#
# If you ever want the raw flat JSON array as well, you can re-enable:
# FEEDS = {
#     "mhnow_raw.json": {
#         "format": "json",
#         "encoding": "utf-8",
#         "indent": 2,
#         "overwrite": True,
#     },
# }

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------
LOG_LEVEL = "INFO"

# ------------------------------------------------------------------
# Miscellaneous
# ------------------------------------------------------------------
# Scrapy 2.x+ recommends explicitly setting a request fingerprinter
# version to avoid deprecation warnings.
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"

TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

FEED_EXPORT_ENCODING = "utf-8"
