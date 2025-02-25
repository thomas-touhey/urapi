#!/usr/bin/make -f

help:
	@echo "Run 'make test' to run tests."

test:
	@rm -rf htmlcov
	@-poetry run pytest $(O) $(SPECIFIC_TESTS)
	@printf "\033[1;32m>\033[0m \033[1m%s\033[0m %s\n" \
		"HTML coverage is available under the following directory:"
	@printf "\033[1;32m>\033[0m \033[1m%s\033[0m %s\n" \
		"file://$(realpath .)/htmlcov/index.html"

.PHONY: help test
