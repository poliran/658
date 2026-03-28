.PHONY: install test clean predict evaluate lint format

# Install dependencies
install:
	pip install -r requirements.txt

# Install in development mode
install-dev:
	pip install -e .
	pip install -r requirements-dev.txt

# Run tests
test:
	python -m pytest tests/ -v

# Run tests with coverage
test-coverage:
	python -m pytest tests/ --cov=src --cov-report=html

# Clean up generated files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf build/ dist/ *.egg-info/
	rm -f evaluation_results.json

# Run prediction
predict:
	python run_prediction.py

# Run model evaluation
evaluate:
	python evaluate_model.py

# Lint code
lint:
	flake8 src/ tests/ --max-line-length=100

# Format code
format:
	black src/ tests/ --line-length=100

# Run all checks
check: lint test

# Setup development environment
setup-dev: install-dev
	@echo "Development environment ready!"
