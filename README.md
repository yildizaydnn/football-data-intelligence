# Football Data Intelligence Platform

API-Football verisini toplayan, işleyen ve analiz eden full-stack platform.

- **Backend:** FastAPI + SQLAlchemy 2.0 + PostgreSQL (katmanlı mimari)
- **Frontend:** Next.js (App Router) + TypeScript
- **Araçlar:** uv, ruff, Alembic, pytest, Docker Compose

## Hızlı başlangıç

```bash
cp .env.example .env      # API_FOOTBALL_KEY değerini doldur
make install              # backend bağımlılıkları
make db-up                # PostgreSQL (localhost:5433)
make migrate              # tabloları oluştur
make dev                  # http://localhost:8000/docs
```

## Komutlar

`make help` tüm komutları listeler.
