FROM python:3-slim

# Set working directory
WORKDIR /app

# Set Python path to use local packages
ENV PYTHONPATH=/app/.python_packages:$PYTHONPATH

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    git \
    && rm -rf /var/lib/apt/lists/*
