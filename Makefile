init: ## initialize environment and install requirements
	pip install pipenv
	pipenv install --dev
	pipenv run python -m nltk.downloader punkt
	pipenv run python -m spacy download en_core_web_trf
	pipenv run python -m spacy download de_core_news_sm

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

lint: ## check style with flake8
	pipenv run flake8 plagdef tests

test-ci: ## run tests, GUI tests excluded
	pipenv run pytest --ignore=plagdef/tests/gui/test_model.py

test-all-ci: ## run tests on every Python version with tox
	pipenv run tox

coverage-ci: ## check code coverage quickly with the default Python
	pipenv run coverage erase
	pipenv run coverage run --source plagdef --omit="*/test*,*/gui/model.py" -m pytest --ignore=plagdef/tests/gui/test_model.py
	pipenv run coverage report -m
	pipenv run coverage xml

run: ## starts the CLI
	pipenv run app.py
