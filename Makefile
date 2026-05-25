.PHONY: install test lint fmt clean run run-api run-frontend docker-up docker-down

# Python backend
install:
	uv sync --frozen False

test:
	uv run pytest tests/ -v

lint:
	uv run ruff check src/

fmt:
	uv run ruff format src/

clean:
	rm -rf .venv build dist *.egg-info src/*.egg-info

run-api:
	uv run uvicorn nl2sql.api:app --host 0.0.0.0 --port 8000 --reload

# React frontend
frontend-install:
	cd frontend && npm install

frontend-test:
	cd frontend && npm run test

frontend-build:
	cd frontend && npm run build

frontend-dev:
	cd frontend && npm run dev

# Docker
docker-up:
	docker compose up --build

docker-down:
	docker compose down

# Full stack
run: run-api

# Install everything
setup: install frontend-install

# Run tests for both
test-all: test frontend-test

# Format everything
fmt-all: fmt
	cd frontend && npm run format