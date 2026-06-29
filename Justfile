set dotenv-load := false
uv-run := "uv run"

default:
    @just --list

clear-dist:
    rm -rf autocrop.egg-info build dist

build: clear-dist
    uv build

test:
    {{ uv-run }} pytest

lint:
    {{ uv-run }} flake8 --max-complexity=10 --count autocrop tests

check: lint test

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
