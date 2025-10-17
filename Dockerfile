# Simple Dockerfile for running FastAPI app
FROM python:3.13-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git gosu \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

COPY . .

# ✅ Create a home directory for appuser
RUN adduser --system --group --uid 1000 --home /home/appuser appuser

# ✅ Set the HOME environment variable
ENV HOME=/home/appuser

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENV GITHUB_TOKEN=""

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uv", "run", "uvicorn", "fastapi_app:app", "--host", "0.0.0.0", "--port", "8000"]
