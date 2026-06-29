set dotenv-load := false
uv-run := "uv run"

default:
    @just --list

clear-dist:
    rm -rf autocrop.egg-info build dist

pypi-test: clear-dist
    uv build
    {{ uv-run }} twine upload dist/* -r testpypi

pypi:
    {{ uv-run }} twine upload dist/*

test:
    {{ uv-run }} pytest

lint:
    {{ uv-run }} flake8 --max-complexity=10 --count autocrop tests

check: lint test

docs:
    {{ uv-run }} portray on_github_pages

venv:
    uv venv

install:
    uv sync

initial_setup: install
    @echo
    @echo "Initial setup successful."
    @echo
    @echo "Activate your environment with: source .venv/bin/activate"
    @echo
    @echo "You can also run commands directly with: uv run ..."
    @echo
