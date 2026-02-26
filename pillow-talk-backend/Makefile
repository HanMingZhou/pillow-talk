.PHONY: install test lint format type-check run docker-build docker-run clean help

help:
	@echo "Pillow Talk Backend - Makefile Commands"
	@echo ""
	@echo "  make install      - Install dependencies"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linting checks"
	@echo "  make format       - Format code"
	@echo "  make type-check   - Run type checking"
	@echo "  make run          - Run development server"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run Docker container"
	@echo "  make clean        - Clean build artifacts"

install:
	poetry install

test:
	poetry run pytest

coverage:
	poetry run pytest --cov=src/pillow_talk --cov-report=html --cov-report=term-missing

lint:
	poetry run ruff check src/ tests/

format:
	poetry run ruff format src/ tests/
	poetry run ruff check --fix src/ tests/

type-check:
	poetry run mypy src/pillow_talk

run:
	poetry run uvicorn pillow_talk.main:app --reload --host 0.0.0.0 --port 8000

docker-build:
	docker build -t pillow-talk-backend:latest .

docker-run:
	docker run -p 8000:8000 --env-file .env pillow-talk-backend:latest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
