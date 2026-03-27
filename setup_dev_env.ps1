<#
.SYNOPSIS
    Set up an isolated development environment for the mhnow Scrapy project.

.DESCRIPTION
    Prompts the user to choose between:
      1) Python virtual environment (.venv) — local, no extra software needed
      2) Docker container               — completely isolated from the host OS

    Both options install all dependencies declared in requirements.txt.

.NOTES
    Run from the project root:
        .\setup_dev_env.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
function Write-Header([string]$msg) {
    Write-Host ""
    Write-Host "===================================================" -ForegroundColor Cyan
    Write-Host "  $msg" -ForegroundColor Cyan
    Write-Host "===================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Confirm-Command([string]$cmd) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Host "ERROR: '$cmd' was not found on PATH. Please install it first." -ForegroundColor Red
        exit 1
    }
}

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
Write-Header "Monster Hunter Now Scraper — Dev Environment Setup"

# ---------------------------------------------------------------------------
# Mode selection
# ---------------------------------------------------------------------------
Write-Host "Choose your development environment:" -ForegroundColor Yellow
Write-Host "  [1]  Python virtual environment  (recommended — no extra software needed)"
Write-Host "  [2]  Docker container             (fully isolated from the host OS)"
Write-Host ""

$choice = ""
while ($choice -notin @("1", "2")) {
    $choice = (Read-Host "Enter 1 or 2").Trim()
}

# ===========================================================================
# MODE 1 — Python virtual environment
# ===========================================================================
if ($choice -eq "1") {
    Write-Header "Setting up Python virtual environment"

    Confirm-Command "python"

    # Verify Python version is 3.8+
    $pyVersion = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    Write-Host "Detected Python $pyVersion"
    $major, $minor = $pyVersion -split "\." | ForEach-Object { [int]$_ }
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 8)) {
        Write-Host "ERROR: Python 3.8 or later is required. Found $pyVersion." -ForegroundColor Red
        exit 1
    }

    # Create virtual environment
    $venvDir = ".venv"
    if (Test-Path $venvDir) {
        Write-Host "Virtual environment '$venvDir' already exists — skipping creation." -ForegroundColor Yellow
    } else {
        Write-Host "Creating virtual environment at $venvDir ..."
        python -m venv $venvDir
        Write-Host "Virtual environment created." -ForegroundColor Green
    }

    # Activate and install dependencies
    Write-Host "Activating virtual environment and installing dependencies ..."
    & "$venvDir\Scripts\Activate.ps1"
    python -m pip install --upgrade pip --quiet
    pip install -r requirements.txt

    Write-Host ""
    Write-Host "Setup complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "To activate the environment manually in future sessions:" -ForegroundColor Yellow
    Write-Host "    .\.venv\Scripts\Activate.ps1"
    Write-Host ""
    Write-Host "To run the scraper:" -ForegroundColor Yellow
    Write-Host "    .\run_scraper.ps1"
    Write-Host "  — or directly —"
    Write-Host "    scrapy crawl mhnow -O mhnow.json"
}

# ===========================================================================
# MODE 2 — Docker
# ===========================================================================
if ($choice -eq "2") {
    Write-Header "Setting up Docker container environment"

    Confirm-Command "docker"

    # Verify Docker daemon is running
    try {
        docker info *>$null
    } catch {
        Write-Host "ERROR: Docker daemon does not appear to be running. Start Docker Desktop and try again." -ForegroundColor Red
        exit 1
    }

    $imageName = "mhnow-scraper"
    $dockerfilePath = "Dockerfile"

    # Generate a minimal Dockerfile if it does not already exist
    if (Test-Path $dockerfilePath) {
        Write-Host "Dockerfile already exists — skipping generation." -ForegroundColor Yellow
    } else {
        Write-Host "Generating Dockerfile ..."
        $dockerfileContent = @"
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
CMD ["scrapy", "crawl", "mhnow", "-O", "mhnow.json"]
"@
        Set-Content -Path $dockerfilePath -Value $dockerfileContent -Encoding UTF8
        Write-Host "Dockerfile created at $dockerfilePath" -ForegroundColor Green
    }

    # Build the Docker image
    Write-Host "Building Docker image '$imageName' (this may take a minute the first time) ..."
    docker build -t $imageName .

    Write-Host ""
    Write-Host "Docker image '$imageName' built successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Useful commands:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Run the scraper (output saved to ./mhnow.json on the host):"
    Write-Host "    docker run --rm -v `"${PWD}:/app`" $imageName"
    Write-Host ""
    Write-Host "  Start an interactive shell inside the container for development:"
    Write-Host "    docker run --rm -it -v `"${PWD}:/app`" $imageName bash"
    Write-Host ""
    Write-Host "  Run Scrapy shell against a URL for selector testing:"
    Write-Host "    docker run --rm -it -v `"${PWD}:/app`" $imageName scrapy shell 'https://monsterhunternow.com/en/monsters'"
    Write-Host ""
    Write-Host "To run the scraper via the helper script:" -ForegroundColor Yellow
    Write-Host "    .\run_scraper.ps1"
}
