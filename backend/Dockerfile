FROM python:3.13-slim

# Build deps for native wheels (cryptography, pandas, etc.)
# Most wheels exist for linux/amd64 and arm64 on PyPI, so this is a fallback.
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps before copying source for better layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app/ ./app/

EXPOSE 8000

# --host 0.0.0.0 is required — binding 127.0.0.1 inside the container
# would make the service unreachable from outside the container.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
