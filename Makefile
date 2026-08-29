.PHONY: validate fixtures test site check quality audit

validate:
	python3 atlas.py validate
	python3 atlas.py safety

fixtures:
	python3 atlas.py run

test:
	python3 -m unittest discover -v

site:
	python3 atlas.py build-site

check:
	python3 atlas.py check
	python3 -m unittest discover -v

quality:
	ruff check .
	ruff format --check .
	mypy
	bandit -q -r atlas.py fixtures

audit: check quality
