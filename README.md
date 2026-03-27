# Monster Hunter Now Scraper

A [Scrapy](https://scrapy.org/) project that scrapes all four data categories
from [monsterhunternow.com](https://monsterhunternow.com):

- **Monsters** — stats, weaknesses, habitats, breakable parts, and materials
- **Weapons** — all weapon types with full upgrade grade/level attack, element,
  and skill data
- **Armor** — all armor pieces with per-grade defense values and skills
- **Skills** — all skills with per-level descriptions and effect amounts

Output is a single `mhnow.json` file grouped by category.

---

## How it works

The site uses a server-side "islands architecture" — all item data is embedded
directly in the raw HTML as HTML-encoded JSON inside
`<root-island props="...">` elements. No JavaScript execution or headless
browser is needed; Scrapy's standard HTTP fetcher retrieves everything in
**4 requests** (one per listing page).

---

## Requirements

- Python 3.12+ **or** Docker / Podman

---

## Quick start

### Option 1 — Python virtual environment (recommended)

1. **Windows (PowerShell)**

    ```powershell
    # First-time setup (creates .venv and installs dependencies)
    .\setup_dev_env.ps1    # choose option 1 when prompted

    # Run the scraper
    .\run_scraper.ps1
    ```

2. **Linux / macOS**

    ```bash
    # First-time setup (creates .venv and installs dependencies)
    ./setup_dev_env.sh     # choose option 1 when prompted

    # Run the scraper
    ./run_scraper.sh
    ```

### Option 2 — Docker or Podman

The setup script auto-detects whichever container runtime is on your `PATH`
(Docker is preferred; Podman is used as a fallback).

1. **Windows (PowerShell)**

    ```powershell
    # First-time setup (builds the container image)
    .\setup_dev_env.ps1    # choose option 2 when prompted

    # Run the scraper
    .\run_scraper.ps1
    ```

2. **Linux / macOS**

    ```bash
    # First-time setup (builds the container image)
    ./setup_dev_env.sh     # choose option 2 when prompted

    # Run the scraper
    ./run_scraper.sh
    ```

The run scripts auto-detect which environment is available (venv takes priority
over container) and use it.

---

## Manual usage

If you prefer to run Scrapy directly:

1. **Windows (PowerShell)**

    ```powershell
    # Activate the venv first
    .venv\Scripts\Activate.ps1

    # Run the spider
    scrapy crawl mhnow
    ```

2. **Linux / macOS**

    ```bash
    # Activate the venv first
    source .venv/bin/activate

    # Run the spider
    scrapy crawl mhnow
    ```

Output is written to `mhnow.json` in the project root.

---

## Output format

```json
{
  "monsters": [
    {
      "category": "monsters",
      "name": "Aknosom",
      "description": "",
      "weaknesses": ["Water"],
      "stats": [
        { "label": "species",   "value": "BIRD" },
        { "label": "element",   "value": "fire" },
        { "label": "min_grade", "value": "3" }
      ],
      "image_urls": ["https://..."],
      "extra_fields": {
        "id": "aknosom",
        "habitat": ["Forest", "Desert"],
        "breakable_parts": ["HEAD"],
        "materials": [{ "name": "Aknosom Scale", "rarity": 1 }]
      },
      "source_url": "https://monsterhunternow.com/en/monsters/aknosom"
    }
  ],
  "weapons": [ "..." ],
  "armor":   [ "..." ],
  "skills":  [ "..." ]
}
```

All four top-level keys are always present, even if empty.

---

## Project structure

```text
mhnow/
├── mhnow_scraper/
│   ├── spiders/
│   │   └── mhnow_spider.py   # Main spider — root-island JSON parsing
│   ├── items.py              # MhnowItem field definitions
│   ├── pipelines.py          # Normalisation + grouped JSON output
│   └── settings.py           # Scrapy settings (AutoThrottle, delays, etc.)
├── scrapy.cfg                # Scrapy project config
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container image definition
├── setup_dev_env.ps1         # One-time environment setup — Windows
├── setup_dev_env.sh          # One-time environment setup — Linux/macOS
├── run_scraper.ps1           # Run the scraper — Windows
└── run_scraper.sh            # Run the scraper — Linux/macOS
```

---

## Settings

Key settings in `mhnow_scraper/settings.py`:

| Setting | Value | Purpose |
| --- | --- | --- |
| `DOWNLOAD_DELAY` | `2` s | Base delay between requests |
| `AUTOTHROTTLE_ENABLED` | `True` | Adjusts delay based on server latency |
| `CONCURRENT_REQUESTS_PER_DOMAIN` | `1` | One request at a time to be polite |
| `RETRY_TIMES` | `3` | Retry failed requests up to 3 times |
| `ROBOTSTXT_OBEY` | `True` | Respects the site's robots.txt |

---

## Extending

To add a new data source:

1. Add an entry to `LISTING_PAGES` in
   `mhnow_scraper/spiders/mhnow_spider.py` mapping the URL to
   `(category, component_name, data_key)`.
2. Add a `_parse_<category>` method to the spider class.
3. Add the new category key to `_KNOWN_CATEGORIES` in `mhnow_scraper/pipelines.py`.
