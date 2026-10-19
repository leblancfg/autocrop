set dotenv-load := false
uv-run := "uv run"

default:
    @just --list

clear-dist:
    rm -rf autocrop.egg-info build dist

build: clear-dist
    uv build

docs:
    #!/usr/bin/env sh
    set -eu
    cfg=$(mktemp)
    trap 'rm -f "$cfg"' EXIT
    printf 'site_name: autocrop\ndocs_dir: "%s/docs"\n' "$PWD" > "$cfg"
    uvx mkdocs serve -f "$cfg" -a 127.0.0.1:8000

test:
    {{ uv-run }} pytest

lint:
    {{ uv-run }} ruff check autocrop tests

format:
    {{ uv-run }} ruff format autocrop tests

format-check:
    {{ uv-run }} ruff format --check autocrop tests

typecheck:
    {{ uv-run }} ty check --error-on-warning

check: lint format-check typecheck test

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
