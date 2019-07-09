RED=\033[0;31m
NC=\033[0m # No Color

pypi-test:
	python setup.py sdist
	twine upload dist/* -r testpypi

pypi: pypi-test
	twine upload dist/*

check:
	@printf "${RED}Running flake8${NC}\n"
	@printf "${RED}Running pytest${NC}\n"
	@flake8 --exclude=./env --max-complexity=8 --count .
	@pytest

.PHONY: check
