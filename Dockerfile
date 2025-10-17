# Simple Dockerfile for running FastAPI app
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies, including su-exec
RUN apt-get update && apt-get install -y --no-install-recommends git su-exec && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv

COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

COPY . .

# Create a non-root user
RUN adduser --system --group --uid 1000 appuser

# Copy and set up the entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# The 'USER appuser' line is correctly removed from here.

EXPOSE 8000
ENV GITHUB_TOKEN=""

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uv", "run", "uvicorn", "fastapi_app:app", "--host", "0.0.0.0", "--port", "8000"]
