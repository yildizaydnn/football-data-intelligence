.PHONY: help install db-up db-down dev migrate migration lint format test

BACKEND := cd backend &&

help: ## Komutları listele
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

install: ## Backend bağımlılıklarını kur
	$(BACKEND) uv sync

db-up: ## PostgreSQL'i başlat
	docker compose up -d db

db-down: ## Container'ları durdur
	docker compose down

dev: ## Backend'i geliştirme modunda çalıştır
	$(BACKEND) uv run uvicorn app.main:app --reload

migrate: ## Migration'ları uygula (alembic upgrade head)
	$(BACKEND) uv run alembic upgrade head

migration: ## Yeni migration üret: make migration m="açıklama"
	$(BACKEND) uv run alembic revision --autogenerate -m "$(m)"

lint: ## Ruff ile lint + format kontrolü
	$(BACKEND) uv run ruff check . && uv run ruff format --check .

format: ## Ruff ile otomatik düzelt + formatla
	$(BACKEND) uv run ruff check --fix . && uv run ruff format .

test: ## Testleri çalıştır
	$(BACKEND) uv run pytest
