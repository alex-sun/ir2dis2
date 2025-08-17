# syntax=docker/dockerfile:1
FROM python:3.12-slim

# System deps (if any)
RUN apt-get update -y && apt-get install -y --no-install-recommends \    tini \  && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \    PYTHONUNBUFFERED=1

WORKDIR /app

# Create non-root user
RUN useradd -m app && mkdir -p /app/data && chown -R app:app /app
USER app

# Dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Project (no code yet; mount during dev or copy when ready)
COPY . /app

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "src/bot.py"]
