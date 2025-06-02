# OSRS Item Data
project for collecting item data from the OSRS Grand Exchange

## Required
- [🐳 Docker](https://www.docker.com/) for project containerization

## Setup / Installation Instructions
~etl/data_collector# docker build -t fetch-ge-wiki-prices .
~item_data# docker-compose up -d --build 

## Interfaces
- [📅 Airflow](http://localhost:8080/home) (admin:admin)
- [📈 Dashboard](http://localhost:8050)

## Backfilling
```
airflow-scheduler# airflow dags backfill ingestion_raw_ge_history -s 2025-05-01T00:00:00 -e 2025-05-02T00:00:00
```