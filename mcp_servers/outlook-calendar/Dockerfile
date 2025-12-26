FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY outlook-calendar/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy base class and server
COPY base.py /app/base.py
COPY outlook-calendar/server.py /app/server.py

# Environment variables (to be set at runtime)
ENV MICROSOFT_CLIENT_ID=""
ENV MICROSOFT_CLIENT_SECRET=""
ENV MICROSOFT_TENANT_ID="common"
ENV PORT=8000

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run server
CMD ["python", "server.py"]
