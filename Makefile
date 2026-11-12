.PHONY: help install db-up db-down dev web migrate migration sync api-types lint format test

BACKEND := cd backend &&

help: ## Komutları listele
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

install: ## Backend ve frontend bağımlılıklarını kur
	$(BACKEND) uv sync
	cd frontend && pnpm install

db-up: ## PostgreSQL'i başlat
	docker compose up -d db

db-down: ## Container'ları durdur
	docker compose down

dev: ## Backend'i geliştirme modunda çalıştır
	$(BACKEND) uv run uvicorn app.main:app --reload

web: ## Frontend'i geliştirme modunda çalıştır (http://localhost:3000)
	cd frontend && pnpm dev

migrate: ## Migration'ları uygula (alembic upgrade head)
	$(BACKEND) uv run alembic upgrade head

migration: ## Yeni migration üret: make migration m="açıklama"
	$(BACKEND) uv run alembic revision --autogenerate -m "$(m)"

sync: ## API-Football'dan tam veri yükle (3 istek). Örn: make sync LEAGUE=39 SEASON=2023
	$(BACKEND) uv run python -m scripts.initial_sync $(if $(LEAGUE),--league $(LEAGUE)) $(if $(SEASON),--season $(SEASON))

api-types: ## Backend OpenAPI şemasından frontend TS tiplerini üret
	$(BACKEND) uv run python -m scripts.export_openapi ../frontend/openapi.json
	cd frontend && pnpm gen:api

lint: ## Backend (ruff) + frontend (eslint, tsc) kontrolleri
	$(BACKEND) uv run ruff check . && uv run ruff format --check .
	cd frontend && pnpm lint && pnpm typecheck

format: ## Ruff ile otomatik düzelt + formatla
	$(BACKEND) uv run ruff check --fix . && uv run ruff format .

test: ## Testleri çalıştır
	$(BACKEND) uv run pytest
