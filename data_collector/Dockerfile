FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
COPY item_data_collector.py .
COPY queue_processor.py .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "item_data_collector.py"]
