.PHONY: help install install-dev test test-unit test-integration lint format typecheck clean run

help:
	@echo "InfoFlowLab - Available commands:"
	@echo "  make install      - Install package with dependencies"
	@echo "  make install-dev  - Install with development dependencies"
	@echo "  make test         - Run all tests"
	@echo "  make test-unit    - Run unit tests only"
	@echo "  make test-cov     - Run tests with coverage report"
	@echo "  make lint         - Run linter (flake8)"
	@echo "  make format       - Format code (black)"
	@echo "  make typecheck    - Run type checker (mypy)"
	@echo "  make clean        - Remove build artifacts and cache"
	@echo "  make run          - Run the application"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

install-full:
	pip install -e ".[full]"

test:
	pytest tests/ -v

test-unit:
	pytest tests/ -v -m unit

test-integration:
	pytest tests/ -v -m integration

test-cov:
	pytest tests/ --cov=src --cov-report=html --cov-report=term

lint:
	flake8 src/ tests/ --max-line-length=100 --extend-ignore=E203,W503

format:
	black src/ tests/ --line-length=100

typecheck:
	mypy src/ --ignore-missing-imports

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '*.egg-info' -exec rm -rf {} +
	find . -type d -name '.pytest_cache' -exec rm -rf {} +
	find . -type d -name '.mypy_cache' -exec rm -rf {} +
	find . -type d -name 'htmlcov' -exec rm -rf {} +
	find . -type d -name 'dist' -exec rm -rf {} +
	find . -type d -name 'build' -exec rm -rf {} +
	rm -f .coverage
	rm -rf logs/*.prof

run:
	python main.py