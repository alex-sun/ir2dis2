#!/bin/bash

echo "=== Running validation checks for iRacing Last Race Details script ==="

# Run ruff check
echo "\n1/3 Running ruff check..."
docker run --rm -v "$(pwd)/src:/app/src" python:3.11-slim bash -c "pip install ruff && cd /app && ruff check src/ --fix"

# Run mypy check
echo "\n2/3 Running mypy check..."
docker run --rm -v "$(pwd)/src:/app/src" python:3.11-slim bash -c "pip install mypy typing-extensions && cd /app && mypy src/ --strict"

# Run pytest
echo "\n3/3 Running pytest..."
docker run --rm -v "$(pwd)/src:/app/src" -v "$(pwd)/tests:/app/tests" python:3.11-slim bash -c "pip install pytest && cd /app && python -m pytest tests/ -v"

echo "\n=== Validation complete ==="