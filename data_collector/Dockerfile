FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
COPY item_data_collector.py .

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "-u", "item_data_collector.py"]
CMD []