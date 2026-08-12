.DEFAULT_GOAL := help
SHELL := /bin/bash

.PHONY: help keys keys-force requirements clean sync install-hooks dev migrate test test-integration lint format typecheck import-lint services services-down

help: ## Показать список доступных целей
	@echo "Доступные цели:"
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'

keys: ## Сгенерировать Ed25519 ключи подписи (пароль берётся из .env)
	./scripts/gen_keys.sh

keys-force: ## Перегенерировать Ed25519 ключи подписи, перезаписав существующие
	./scripts/gen_keys.sh -f

requirements: ## Сгенерировать requirements.txt и requirements-dev.txt
	./scripts/compile_pip.sh

clean: ## Удалить все каталоги __pycache__ в src/
	./scripts/clear_pycache.sh

sync: ## Установить зависимости: uv sync --group dev
	uv sync --group dev

install-hooks: ## Установить git-хуки pre-commit
	uv run pre-commit install

dev: ## Запустить сервер разработки
	uv run fastapi dev ./src/composition/fastapi.py

migrate: ## Применить миграции Alembic
	uv run alembic upgrade head

test: ## Запустить unit-тесты
	uv run pytest -m "not integration"

test-integration: ## Запустить интеграционные тесты (нужны make services)
	uv run pytest -m integration

lint: ## Проверить код линтером ruff
	uv run ruff check .

format: ## Отформатировать код и исправить ошибки (ruff)
	uv run ruff format . && uv run ruff check . --fix

typecheck: ## Проверить типы (basedpyright)
	uv run basedpyright

import-lint: ## Проверить архитектурные контракты (import-linter)
	uv run lint-imports

services: ## Запустить PostgreSQL, Redis и MinIO в Docker
	docker compose --env-file .env up elyria-postgres elyria-redis elyria-minio -d --wait

services-down: ## Остановить сервисы Docker
	docker compose --env-file .env down
