FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}"

WORKDIR /app

# System dependencies for yt-dlp (ffmpeg for media handling)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Install uv for fast, lockfile-resolved dependency management
RUN pip install --no-cache-dir uv

# Install Python dependencies first to leverage build cache
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --locked --no-dev

# Copy application code
COPY . .

# Default command: requires BOT_TOKEN to be provided at runtime
CMD ["python", "main.py"]
