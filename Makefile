COMPOSE_FILE = docker-compose.yml
BACKFILL_DAG_NAME ?= ingestion_raw_ge_history
BACKFILL_DATE ?=

.PHONY: init-project up down backfill dbup dashup airflow-cleanup refresh-dashboard

init-project:
	@

up:
	docker-compose -f $(COMPOSE_FILE) up -d

down:
	docker-compose -f $(COMPOSE_FILE) down

backfill:
	@if [ -n "$(BACKFILL_DATE)" ]; then \
		START_DATE=$$(date -u -d "$(BACKFILL_DATE)" +%Y-%m-%dT00:00:00); \
		END_DATE=$$(date -u -d "$$(date -u -d "$(BACKFILL_DATE) +1 day" +%Y-%m-%d)" +%Y-%m-%dT00:00:00); \
		echo "Running backfill for full day: $(BACKFILL_DATE)"; \
	else \
		START_DATE=$$(date -u -d '24 hours ago' +%Y-%m-%dT%H:00:00); \
		END_DATE=$$(date -u +%Y-%m-%dT%H:00:00); \
		echo "Running backfill for the last 24 hours"; \
	fi; \
	echo "From: $$START_DATE to $$END_DATE"; \
	docker-compose -f $(COMPOSE_FILE) exec airflow-scheduler airflow dags backfill $(BACKFILL_DAG_NAME) -s $$START_DATE -e $$END_DATE

dbup:
	docker-compose -f $(COMPOSE_FILE) up osrs-database -d

dashup:
	docker-compose -f $(COMPOSE_FILE) up dashboard -d

airflow-cleanup:
	docker-compose -f $(COMPOSE_FILE) exec airflow-webserver \
	 	airflow tasks clear "$(BACKFILL_DAG_NAME)" --yes

refresh-dashboard:
	docker-compose -f $(COMPOSE_FILE) restart dashboard