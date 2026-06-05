.PHONY: all generate validate

PYTHON ?= python3

all: generate validate

generate:
	$(PYTHON) scripts/generate_synthetic_math_department.py

validate:
	$(PYTHON) scripts/validate_synthetic_math_department.py
