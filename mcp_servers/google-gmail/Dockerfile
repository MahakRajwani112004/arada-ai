FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy base class and server
COPY ../base.py /app/base.py
COPY server.py /app/server.py

# Environment variables (to be set at runtime)
ENV GOOGLE_CLIENT_ID=""
ENV GOOGLE_CLIENT_SECRET=""

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run server
CMD ["python", "server.py"]
