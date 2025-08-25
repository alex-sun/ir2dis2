FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir aiohttp pytest pytest-asyncio

# Copy source code
COPY src/ ./src/
COPY tests/ ./tests/
COPY .roo/ ./.roo/

# Set environment variables for testing (using dummy values)
ENV IRACING_EMAIL="test@example.com"
ENV IRACING_PASSWORD="password123"
ENV IRACING_CUSTOMER_ID=123456

# Default command to run tests
CMD ["python", "-m", "pytest", "tests/", "-v"]