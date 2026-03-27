<#
.SYNOPSIS
    Run the Monster Hunter Now Scrapy spider.

.DESCRIPTION
    Auto-detects the development environment (Python virtual environment or
    Docker) and executes:

        scrapy crawl mhnow -O mhnow.json

    Output is written to mhnow.json in the project root.

    Environment detection priority:
      1.  Python virtual environment   (.venv\Scripts\Activate.ps1 exists)
      2.  Docker image                 (image named 'mhnow-scraper' is present)

    If neither environment is found the script prints setup instructions
    and exits cleanly.

.NOTES
    Run from the project root:
        .\run_scraper.ps1
#>

[CmdletBinding()]
[System.Diagnostics.CodeAnalysis.SuppressMessageAttribute(
    'PSAvoidUsingWriteHost', '',
    Justification = 'Interactive console script - colored output is intentional.'
)]
param()

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

# GroupedOutputPipeline in pipelines.py writes mhnow.json directly.
# Do NOT pass -O / -o flags here - they re-enable the flat-array FEEDS
# exporter which would overwrite the grouped output.
$scraperCommand = "scrapy crawl mhnow"
$imageName      = "mhnow-scraper"
$venvActivate   = ".venv\Scripts\Activate.ps1"

Write-Header "Monster Hunter Now Scraper"

# ---------------------------------------------------------------------------
# Priority 1 - Python virtual environment
# ---------------------------------------------------------------------------
if (Test-Path $venvActivate) {
    Write-Host "Detected environment: Python virtual environment (.venv)" -ForegroundColor Green
    Write-Host "Activating .venv ..."
    & $venvActivate

    Write-Host "Running: $scraperCommand"
    Write-Host ""
    scrapy crawl mhnow

    Write-Host ""
    Write-Host "Done! Output written to mhnow.json" -ForegroundColor Green
    exit 0
}

# ---------------------------------------------------------------------------
# Priority 2 - Docker
# ---------------------------------------------------------------------------
if (Get-Command "docker" -ErrorAction SilentlyContinue) {
    # Check whether the image has been built
    $imageExists = docker images -q $imageName 2>$null
    if ($imageExists) {
        Write-Host "Detected environment: Docker image '$imageName'" -ForegroundColor Green
        Write-Host "Running scraper inside Docker container ..."
        Write-Host ""

        # Mount the current directory into /app so mhnow.json is written
        # back to the host file system.
        docker run --rm -v "${PWD}:/app" $imageName $scraperCommand.Split(" ")

        Write-Host ""
        Write-Host "Done! Output written to mhnow.json" -ForegroundColor Green
        exit 0
    }
}

# ---------------------------------------------------------------------------
# No environment found
# ---------------------------------------------------------------------------
Write-Host "ERROR: No development environment found." -ForegroundColor Red
Write-Host ""
Write-Host "Run the setup script first to create one:" -ForegroundColor Yellow
Write-Host "    .\setup_dev_env.ps1"
Write-Host ""
Write-Host "The setup script will guide you through creating either:"
Write-Host "  * A Python virtual environment (.venv)"
Write-Host "  * A Docker container image ($imageName)"
exit 1
