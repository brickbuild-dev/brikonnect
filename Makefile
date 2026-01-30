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
	cd backend && pytest -q

fmt:
	cd backend && ruff check --fix .
