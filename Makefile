COMPOSE_FILE = docker-compose.yml

.PHONY: up down

up:
	docker-compose -f $(COMPOSE_FILE) up -d

down:
	docker-compose -f $(COMPOSE_FILE) down
