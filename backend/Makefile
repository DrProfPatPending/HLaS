SHELL := /bin/bash

VENV_PYTHON := ../backend-venv/bin/python

.PHONY: test

test:
	@if [ -x "$(VENV_PYTHON)" ]; then \
		$(VENV_PYTHON) -m unittest discover -s tests -p "test_*.py"; \
	else \
		python -m unittest discover -s tests -p "test_*.py"; \
	fi
