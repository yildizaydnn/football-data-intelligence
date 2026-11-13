#!/bin/sh
# Uygulama açılmadan önce veritabanı şemasını günceller (idempotent: güncelse bir şey yapmaz).
set -e
alembic upgrade head
exec "$@"
