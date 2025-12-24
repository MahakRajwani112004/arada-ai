FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server.py .
COPY ../base.py .

# Expose port
EXPOSE 8002

# Run server
CMD ["python", "server.py"]
