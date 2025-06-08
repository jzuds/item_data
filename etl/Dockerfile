FROM python:3.11-slim

LABEL maintainer="zuds" \
      version="1.0" \
      description="osrs wiki item collector"

WORKDIR /app

COPY requirements.txt .

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt

COPY fetch_ge_wiki_prices.py .
COPY .env .


RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "-u", "fetch_ge_wiki_prices.py"]
CMD []