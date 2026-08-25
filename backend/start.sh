#!/usr/bin/env sh
set -eu

export PYTHONPATH=/app
alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
