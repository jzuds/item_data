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

run on airflow-scheduler to fetch a range of 5 minute intervals
```
airflow dags backfill ingestion_raw_ge_history -s 2025-06-01T00:00:00 -e 2025-06-02T16:00:00
```

run on airflow-scheduler to fetch a single 5 minute interval
```
airflow dags backfill ingestion_raw_ge_history -s 2025-05-01T23:55:00
```

## Debugging
- The permission issue with docker_url='unix://var/run/docker.sock'
```
$ getent group docker
docker:x:1001:zuds
group_add:
- 1001
```