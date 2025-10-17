# Simple Dockerfile for running FastAPI app
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY requirements.txt .
RUN uv pip install --system -r requirements.txt [cite: 2]

COPY . .

# Create a non-root user with a known home directory
RUN adduser --system --group --uid 1000 appuser
RUN chown -R appuser:appuser /app

# Copy and set up the entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# This user will be modified by the entrypoint at runtime
USER appuser

EXPOSE 8000

# Use environment variable for GitHub token
ENV GITHUB_TOKEN=""

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uv", "run", "uvicorn", "fastapi_app:app", "--host", "0.0.0.0", "--port", "8000"]