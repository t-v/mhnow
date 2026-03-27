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
