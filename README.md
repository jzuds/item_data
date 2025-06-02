# OSRS Item Data
project for collecting item data from the OSRS Grand Exchange

## Required
- [🐳 Docker](https://www.docker.com/) for project containerization

## Interfaces
- [📅 Airflow](http://localhost:8080/home) (admin:admin)
- [📈 Dashboard](http://localhost:8050)

## Helpful Commands
~etl/data_collector# docker build -t fetch-ge-wiki-prices .
~item_data# docker-compose up -d --build

## Backfilling
- 5 minute interval = 1 request
- 1 hour = 12 requests
- 1 day = 288 requests

```
airflow-scheduler# airflow dags backfill ingestion_raw_ge_history -s 2025-05-01T00:00:00 -e 2025-05-02T00:00:00
```

## Debugging
- The permission issue with docker_url='unix://var/run/docker.sock'
```
$ getent group docker
docker:x:1001:zuds
group_add:
- 1001
```