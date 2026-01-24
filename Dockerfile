FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Env defaults
ENV PYTHONPATH=/app

# Start command - bind to 0.0.0.0 so Railway can route traffic
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"

