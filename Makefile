.ONESHELL:

RED=\033[0;31m
CYAN=\033[0;36m
NC=\033[0m # No Color

clear-dist:
	rm -rf autocrop.egg-info build dist

pypi-test: clear-dist
	python setup.py sdist bdist_wheel
	twine upload dist/* -r testpypi

pypi:
	twine upload dist/*

test:
	@printf "\n${CYAN} ► Running pytest${NC}\n"
	@pytest

test-all:
	@printf "\n${CYAN} ► Running tox test on all Python versions${NC}\n"
	tox

lint:
	@printf "\n${CYAN} ► Running flake8${NC}\n"
	@flake8 --max-complexity=10 --count autocrop tests

check: lint test

docs:
	portray on_github_pages

venv:
	test -d env || python -m venv env

install:
	( \
	. env/bin/activate; \
	pip install -r requirements.txt; \
	pip install -r requirements-dev.txt; \
	python setup.py install; \
	)

initial_setup: venv install
	@printf "\n\n"
	@printf "${CYAN} ► Initial setup successful.${NC}\n\n"
	@printf "${CYAN} ► Activate your environment with: ${RED}source env/bin/activate${NC}\n\n"
	@printf "${CYAN} ► Once you're done, deactivate with: ${RED}deactivate${NC}\n\n"

.PHONY: pypi-test pypi test test-all lint check docs venv install initial_setup
