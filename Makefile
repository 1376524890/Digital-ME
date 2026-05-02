.PHONY: dev dev-db dev-backend dev-frontend test build clean

dev:
	docker compose up -d postgres redis
	docker compose up backend frontend

dev-db:
	docker compose up -d postgres redis

dev-backend:
	docker compose up backend

dev-frontend:
	cd frontend && pnpm dev

test:
	docker compose run --rm backend pytest

build:
	docker compose build

clean:
	docker compose down -v
	rm -rf frontend/.next frontend/node_modules
	rm -rf backend/__pycache__ backend/src/**/__pycache__
