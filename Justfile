set dotenv-load := false

default:
    @just --list

clear-dist:
    rm -rf autocrop.egg-info build dist

pypi-test: clear-dist
    python setup.py sdist bdist_wheel
    twine upload dist/* -r testpypi

pypi:
    twine upload dist/*

test:
    pytest

test-all:
    tox

lint:
    flake8 --max-complexity=10 --count autocrop tests

check: lint test

docs:
    portray on_github_pages

venv:
    test -d env || python3 -m venv env

install:
    #!/usr/bin/env bash
    set -euo pipefail
    . env/bin/activate
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    python setup.py install

initial_setup: venv install
    @echo
    @echo "Initial setup successful."
    @echo
    @echo "Activate your environment with: source env/bin/activate"
    @echo
    @echo "Once you are done, deactivate with: deactivate"
    @echo
