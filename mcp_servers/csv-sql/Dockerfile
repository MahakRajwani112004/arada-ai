FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY csv-sql/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy base MCP server class
COPY base.py .

# Copy server code
COPY csv-sql/server.py .

# Expose port
EXPOSE 8003

# Run server
CMD ["python", "server.py"]
