#!/bin/bash
set -e

until PGPASSWORD=$DB_PASS psql -h "db" -U "postgres" -d "postgres" -c '\q'; do
  echo >&2 "Postgres is unavailable - sleeping"
  sleep 1
done

echo >&2 "Postgres is up - continuing"

alembic revision --autogenerate -m "Database created"
alembic upgrade head
python3 -m src.bot.start.py