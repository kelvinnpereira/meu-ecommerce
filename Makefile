.PHONY: up down test format logs seed seed-volume

up:
	docker compose up --build -d

down:
	docker compose down --volumes

logs:
	docker compose logs -f

test:
	docker compose exec backend pytest -v

format:
	docker compose exec backend ruff check --fix .
	docker compose exec backend black .

seed:
	docker compose exec backend python -m app.scripts.seed

seed-volume:
	docker compose exec backend python -m app.scripts.seed_volume

