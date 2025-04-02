FROM python:3.9-slim

WORKDIR /app

# Install system dependencies required for web scraping and archiving
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    git \
    chromium \
    chromium-driver \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create a non-root user
RUN useradd -m archivist
RUN chown -R archivist:archivist /app

# Create data directory with proper permissions
RUN mkdir -p /data/archives
RUN chown -R archivist:archivist /data/archives

# Switch to non-root user
USER archivist

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/home/archivist/.local/bin:${PATH}"

# Entry point
ENTRYPOINT ["python", "src/main.py"] 