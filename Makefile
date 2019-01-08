RED=\033[0;31m
NC=\033[0m # No Color

check:
	@printf "${RED}Running flake8${NC}\n"
	@flake8 --exclude=./env --count .
	@printf "${RED}Running pytest${NC}\n"
	@pytest

.PHONY: check
