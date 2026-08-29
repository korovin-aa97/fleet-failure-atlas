.PHONY: validate fixtures test site check

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
