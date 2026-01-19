FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for geospatial libraries
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libgdal-dev \
    gdal-bin \
    && rm -rf /var/lib/apt/lists/*

# Set GDAL environment variables
ENV GDAL_CONFIG=/usr/bin/gdal-config

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run worker
CMD ["python", "-m", "worker.main"]
