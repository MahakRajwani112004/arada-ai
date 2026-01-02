FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY filesystem/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy base class and server
COPY base.py /app/base.py
COPY filesystem/server.py /app/server.py

# Create data directory for file operations
RUN mkdir -p /data /tmp

# Environment variables
ENV PORT=8000

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run server
CMD ["python", "server.py"]
