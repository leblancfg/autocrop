JUST ?= just

clear-dist pypi-test pypi test lint check docs venv install initial_setup:
	@command -v $(JUST) >/dev/null || { \
		echo "The Makefile is kept for compatibility. Install just and run 'just $@'."; \
		exit 127; \
	}
	@$(JUST) $@

.PHONY: clear-dist pypi-test pypi test test-all lint check docs venv install initial_setup
