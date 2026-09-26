.PHONY: install lint test quality sample-report

install:
	python -m pip install -e ".[dev]"

lint:
	ruff check .

test:
	pytest

quality: lint test

sample-report:
	payment-log-analyzer examples/sample-payments.csv --output sample-report.md
