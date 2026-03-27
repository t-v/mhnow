#!/usr/bin/env bash
# setup_dev_env.sh
#
# Set up an isolated development environment for the mhnow Scrapy project.
#
# Prompts the user to choose between:
#   1) Python virtual environment (.venv) — local, no extra software needed
#   2) Docker container               — completely isolated from the host OS
#
# Both options install all dependencies declared in requirements.txt.
#
# Usage (from the project root):
#     ./setup_dev_env.sh

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

confirm_command() {
    if ! command -v "$1" &>/dev/null; then
        echo "ERROR: '$1' was not found on PATH. Please install it first." >&2
        exit 1
    fi
}

# Detect Docker or Podman; prints the CLI name or exits with an error.
get_container_cli() {
    if command -v docker &>/dev/null; then
        echo "docker"
    elif command -v podman &>/dev/null; then
        echo "podman"
    else
        echo "ERROR: Neither 'docker' nor 'podman' was found on PATH. Please install one of them first." >&2
        exit 1
    fi
}

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
print_header "Monster Hunter Now Scraper — Dev Environment Setup"

# ---------------------------------------------------------------------------
# Mode selection
# ---------------------------------------------------------------------------
echo "Choose your development environment:"
echo "  [1]  Python virtual environment  (recommended — no extra software needed)"
echo "  [2]  Container image             (Docker or Podman — fully isolated from the host OS)"
echo ""

choice=""
while [[ "$choice" != "1" && "$choice" != "2" ]]; do
    read -rp "Enter 1 or 2: " choice
    choice="${choice//[[:space:]]/}"
done

# ===========================================================================
# MODE 1 — Python virtual environment
# ===========================================================================
if [ "$choice" = "1" ]; then
    print_header "Setting up Python virtual environment"

    confirm_command "python3"

    # Verify Python version is 3.8+
    PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    echo "Detected Python $PY_VERSION"
    PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
    if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 8 ]; }; then
        echo "ERROR: Python 3.8 or later is required. Found $PY_VERSION." >&2
        exit 1
    fi

    # Create virtual environment
    VENV_DIR=".venv"
    if [ -d "$VENV_DIR" ]; then
        echo "Virtual environment '$VENV_DIR' already exists — skipping creation."
    else
        echo "Creating virtual environment at $VENV_DIR ..."
        python3 -m venv "$VENV_DIR"
        echo "Virtual environment created."
    fi

    # Activate and install dependencies
    echo "Activating virtual environment and installing dependencies ..."
    # shellcheck source=.venv/bin/activate
    source "$VENV_DIR/bin/activate"
    python3 -m pip install --upgrade pip --quiet
    pip install -r requirements.txt

    echo ""
    echo "Setup complete!"
    echo ""
    echo "To activate the environment manually in future sessions:"
    echo "    source .venv/bin/activate"
    echo ""
    echo "To run the scraper:"
    echo "    ./run_scraper.sh"
    echo "  — or directly —"
    echo "    scrapy crawl mhnow"
fi

# ===========================================================================
# MODE 2 — Container (Docker or Podman)
# ===========================================================================
if [ "$choice" = "2" ]; then
    print_header "Setting up container environment"

    CONTAINER_CLI=$(get_container_cli)
    echo "Using container runtime: $CONTAINER_CLI"

    # Verify the daemon / service is running
    if ! $CONTAINER_CLI info &>/dev/null; then
        echo "ERROR: '$CONTAINER_CLI' does not appear to be running. Start it and try again." >&2
        exit 1
    fi

    IMAGE_NAME="mhnow-scraper"
    DOCKERFILE_PATH="Dockerfile"

    # Generate a minimal Dockerfile if it does not already exist
    if [ -f "$DOCKERFILE_PATH" ]; then
        echo "Dockerfile already exists — skipping generation."
    else
        echo "Generating Dockerfile ..."
        cat > "$DOCKERFILE_PATH" <<'EOF'
# -------------------------------------------------------
# Monster Hunter Now Scraper — Docker image
# Base: official Python 3.12 slim image
# -------------------------------------------------------
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Copy dependency manifest first (enables Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# Default command: run the spider and write output to /app/mhnow.json
CMD ["scrapy", "crawl", "mhnow"]
EOF
        echo "Dockerfile created at $DOCKERFILE_PATH"
    fi

    # Build the container image
    echo "Building container image '$IMAGE_NAME' (this may take a minute the first time) ..."
    $CONTAINER_CLI build -t "$IMAGE_NAME" .

    echo ""
    echo "Container image '$IMAGE_NAME' built successfully!"
    echo ""
    echo "Useful commands:"
    echo ""
    echo "  Run the scraper (output saved to ./mhnow.json on the host):"
    echo "    $CONTAINER_CLI run --rm -v \"\$(pwd):/app\" $IMAGE_NAME"
    echo ""
    echo "  Start an interactive shell inside the container for development:"
    echo "    $CONTAINER_CLI run --rm -it -v \"\$(pwd):/app\" $IMAGE_NAME bash"
    echo ""
    echo "  Run Scrapy shell against a URL for selector testing:"
    echo "    $CONTAINER_CLI run --rm -it -v \"\$(pwd):/app\" $IMAGE_NAME scrapy shell 'https://monsterhunternow.com/en/monsters'"
    echo ""
    echo "To run the scraper via the helper script:"
    echo "    ./run_scraper.sh"
fi
