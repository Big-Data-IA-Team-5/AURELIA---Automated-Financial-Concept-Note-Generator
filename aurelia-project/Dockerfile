
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Download Cloud SQL Proxy
RUN wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O /usr/local/bin/cloud_sql_proxy && \
    chmod +x /usr/local/bin/cloud_sql_proxy

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY config/ /app/config/
COPY src/api/ /app/src/api/

# Set Python path
ENV PYTHONPATH=/app
ENV PORT=8000
ENV ENVIRONMENT=production

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run script
CMD if [ -n "$INSTANCE_CONNECTION_NAME" ]; then \
        echo "Starting Cloud SQL Proxy for $INSTANCE_CONNECTION_NAME..." && \
        cloud_sql_proxy -instances=$INSTANCE_CONNECTION_NAME=tcp:5432 & \
        sleep 5; \
    fi && \
    cd /app/src/api && \
    exec uvicorn main:app --host 0.0.0.0 --port ${PORT}
