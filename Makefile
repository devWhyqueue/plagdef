init: ## initialize environment and install requirements
	sudo apt-get install libmagic1
	pip install pipenv
	pipenv install --dev

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

lint: ## check style with flake8
	pipenv run flake8 plagdef tests

test-ci: ## run tests, GUI tests excluded
	pipenv run pytest

test-all-ci: ## run tests on every Python version with tox
	pipenv run tox

coverage-ci: ## check code coverage quickly with the default Python
	pipenv run coverage erase
	pipenv run coverage run --source plagdef --omit="*/test*" -m pytest
	pipenv run coverage report -m
	pipenv run coverage xml

run: ## starts the CLI
	pipenv run app.py
