.PHONY: install test lint typecheck coverage demo check

install:
	python -m pip install -e ".[dev]"

test:
	python -m unittest discover -s tests -v

lint:
	ruff check sentinel_review

typecheck:
	mypy

coverage:
	coverage run -m unittest discover -s tests
	coverage report

demo:
	python -m sentinel_review.demo demo.xlsx
	python -m sentinel_review.cli --db demo.sqlite review demo.xlsx --event DEMO-1 --tenant T-DEMO-A --out demo-out.json
	python -m sentinel_review.cli --db demo.sqlite obligations --tenant T-DEMO-B

check: lint test
