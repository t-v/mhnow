#!/usr/bin/env bash
# run_scraper.sh
#
# Run the Monster Hunter Now Scrapy spider.
#
# Auto-detects the development environment (Python virtual environment or
# Docker) and executes:
#
#     scrapy crawl mhnow
#
# Output is written to mhnow.json in the project root.
#
# Environment detection priority:
#   1.  Python virtual environment   (.venv/bin/activate exists)
#   2.  Docker image                 (image named 'mhnow-scraper' is present)
#
# If neither environment is found the script prints setup instructions
# and exits cleanly.
#
# Usage (from the project root):
#     ./run_scraper.sh

set -euo pipefail

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
print_header() {
    echo ""
    echo "==================================================="
    echo "  $1"
    echo "==================================================="
    echo ""
}

SCRAPER_COMMAND="scrapy crawl mhnow"
IMAGE_NAME="mhnow-scraper"
VENV_ACTIVATE=".venv/bin/activate"

print_header "Monster Hunter Now Scraper"

# ---------------------------------------------------------------------------
# Priority 1 — Python virtual environment
# ---------------------------------------------------------------------------
if [ -f "$VENV_ACTIVATE" ]; then
    echo "Detected environment: Python virtual environment (.venv)"
    echo "Activating .venv ..."
    # shellcheck source=.venv/bin/activate
    source "$VENV_ACTIVATE"

    echo "Running: $SCRAPER_COMMAND"
    echo ""
    eval "$SCRAPER_COMMAND"

    echo ""
    echo "Done! Output written to mhnow.json"
    exit 0
fi

# ---------------------------------------------------------------------------
# Priority 2 — Docker
# ---------------------------------------------------------------------------
if command -v docker &>/dev/null; then
    IMAGE_ID=$(docker images -q "$IMAGE_NAME" 2>/dev/null)
    if [ -n "$IMAGE_ID" ]; then
        echo "Detected environment: Docker image '$IMAGE_NAME'"
        echo "Running scraper inside Docker container ..."
        echo ""

        # Mount the current directory into /app so mhnow.json is written
        # back to the host file system.
        docker run --rm -v "$(pwd):/app" "$IMAGE_NAME" $SCRAPER_COMMAND

        echo ""
        echo "Done! Output written to mhnow.json"
        exit 0
    fi
fi

# ---------------------------------------------------------------------------
# No environment found
# ---------------------------------------------------------------------------
echo "ERROR: No development environment found." >&2
echo ""
echo "Run the setup script first to create one:"
echo "    ./setup_dev_env.sh"
echo ""
echo "The setup script will guide you through creating either:"
echo "  • A Python virtual environment (.venv)"
echo "  • A Docker container image ($IMAGE_NAME)"
exit 1
