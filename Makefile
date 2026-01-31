.PHONY: up down logs migrate test fmt

up:
	docker compose up --build

down:
	docker compose down -v

logs:
	docker compose logs -f api

migrate:
	docker compose exec api alembic upgrade head

test:
	cd apps/api && pytest -q

fmt:
	cd apps/api && ruff check --fix .
