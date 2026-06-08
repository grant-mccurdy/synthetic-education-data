.PHONY: all generate validate warehouse analytics-install postgres-install supabase-load-dry-run supabase-load supabase-validate supabase-validation-narrative postgres-load-dry-run postgres-load calibrate-grade-level

PYTHON ?= python3

all: generate validate

generate:
	$(PYTHON) scripts/generate_synthetic_math_department.py

validate:
	$(PYTHON) scripts/validate_synthetic_math_department.py

analytics-install:
	$(PYTHON) -m pip install -r requirements-analytics.txt || $(PYTHON) -m pip install --user --break-system-packages -r requirements-analytics.txt

warehouse:
	$(PYTHON) scripts/build_duckdb_warehouse.py

postgres-install:
	$(PYTHON) -m pip install -r requirements-postgres.txt || $(PYTHON) -m pip install --user --break-system-packages -r requirements-postgres.txt

supabase-load-dry-run:
	$(PYTHON) scripts/load_supabase_postgres.py --dry-run

supabase-load:
	$(PYTHON) scripts/load_supabase_postgres.py

supabase-validate:
	$(PYTHON) scripts/load_supabase_postgres.py --validate-only

supabase-validation-narrative:
	$(PYTHON) scripts/generate_supabase_pipeline_narrative.py

postgres-load-dry-run: supabase-load-dry-run

postgres-load: supabase-load

calibrate-grade-level:
	@test -n "$(SOURCE_GRADEBOOK)" || (echo "Set SOURCE_GRADEBOOK=/path/to/private/gradebook.csv"; exit 1)
	$(PYTHON) scripts/calibrate_grade_level_effect.py --source-gradebook "$(SOURCE_GRADEBOOK)"
