SHELL := /bin/bash

ROOT_DIR := .
BACKEND_DIR := backend
FRONTEND_DIR := frontend

PROD_ENV := .env.prod
DEV_ENV  := .env.dev
PROD_COMPOSE := docker-compose.prod.yml
DEV_COMPOSE := docker-compose.dev.yml

DC_PROD := docker compose --env-file $(PROD_ENV) -f $(PROD_COMPOSE)
DC_DEV := docker compose --env-file $(DEV_ENV) -f $(PROD_COMPOSE) -f $(DEV_COMPOSE)

.PHONY: help \
	backend-test frontend-build check \
	dev-build dev-up dev-down dev-ps dev-logs dev-health \
	prod-build prod-up prod-down prod-ps prod-logs prod-health \
	development dev-rebuild production \
	clubs-build clubs-check clubs-scaffold-copy \
	sync-field-order-from-db \
	docker-prune \
	ios-sim ios-release clean

help:
	@echo "HLaS master Makefile"
	@echo ""
	@echo "Component targets:"
	@echo "  make backend-test              Run backend tests"
	@echo "  make frontend-build            Build frontend"
	@echo "  make check                     Run local check workflow"
	@echo ""
	@echo "Environment targets:"
	@echo "  make development               Dev overlay cycle (build+up+health)"
	@echo "  make dev-rebuild               Rebuild containers and restart (no tests)"
	@echo "  make docker-prune              Remove stopped containers, unused images and build cache"
	@echo "  make production                Prod cycle (build+up+health)"
	@echo "  make dev-up|dev-down|dev-health|dev-logs|dev-ps"
	@echo "  make prod-up|prod-down|prod-health|prod-logs|prod-ps"
	@echo ""
	@echo "Utilities:"
	@echo "  make clubs-build              Build clubs.config.json from split club sources"
	@echo "  make clubs-check              Validate split club sources via manifest"
	@echo "  make clubs-scaffold-copy      Scaffold split folders + copy logos/backgrounds/photos"
	@echo "  make sync-field-order-from-db  Sync field_order from live Postgres to JSON"
	@echo ""
	@echo "iOS:"
	@echo "  make ios-sim | ios-release | clean"
	@echo "  make ios-sim IOS_SIMULATOR=\"iPhone 16 Pro\""

backend-test:
	$(MAKE) -C $(BACKEND_DIR) test

frontend-build:
	$(MAKE) -C $(FRONTEND_DIR) build

check: backend-test

dev-build:
	$(DC_DEV) build backend frontend

dev-up:
	$(DC_DEV) up -d

dev-down:
	$(DC_DEV) down

dev-ps:
	$(DC_DEV) ps

dev-logs:
	$(DC_DEV) logs --tail=150

dev-health:
	./health_check_dev.sh

prod-build:
	$(DC_PROD) build backend frontend

prod-up:
	$(DC_PROD) up -d

prod-down:
	$(DC_PROD) down

prod-ps:
	$(DC_PROD) ps

prod-logs:
	$(DC_PROD) logs --tail=150

prod-health:
	./health_check_prod.sh

development: check frontend-build dev-build dev-up dev-health

dev-rebuild: dev-build dev-up dev-health

docker-prune:
	docker system prune -f

production: prod-build prod-up prod-health

clubs-build:
	python backend/build_clubs_config.py

clubs-check:
	python backend/build_clubs_config.py --check

clubs-scaffold-copy:
	python backend/scaffold_club_layout.py --copy-logos --copy-backgrounds --copy-member-photos

sync-field-order-from-db:
	./sync_field_order_postgres_to_json.sh

ios-sim:
	$(MAKE) -C $(FRONTEND_DIR) ios-sim IOS_SIMULATOR="$(IOS_SIMULATOR)"

ios-release:
	$(MAKE) -C $(FRONTEND_DIR) ios-release

clean:
	$(MAKE) -C $(FRONTEND_DIR) clean
