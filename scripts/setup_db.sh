#!/bin/bash
set -e

echo "Starting PostgreSQL..."
docker compose up -d postgres
sleep 3

echo "Running migrations..."
docker compose run --rm backend alembic upgrade head

echo "Database setup complete!"
