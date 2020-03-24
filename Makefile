RED=\033[0;31m
NC=\033[0m # No Color

pypi-test:
	python setup.py sdist
	twine upload dist/* -r testpypi

pypi:
	twine upload dist/*

check:
	@printf "${RED}Running flake8${NC}\n"
	@flake8 --exclude=./env --max-complexity=8 --count .
	@printf "${RED}Running pytest${NC}\n"
	@pytest

docs:
	portray on_github_pages

initial_setup:
	# OS-dependent; assumes *nix and python==PY3
	deactivate
	python -m venv env
	source env/bin/activate
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

.PHONY: check pypi pypi-test docs initial_setup
