SHELL := /bin/bash

VENV_DIR := ../backend-venv
VENV_PYTHON := $(VENV_DIR)/bin/python
VENV_MARKER := $(VENV_DIR)/.installed

.PHONY: venv clean-venv test

venv:
	@if [ ! -f "$(VENV_MARKER)" ]; then \
		echo "Creating backend venv..."; \
		rm -rf $(VENV_DIR); \
		python3 -m venv $(VENV_DIR); \
		$(VENV_DIR)/bin/pip install --upgrade pip; \
		$(VENV_DIR)/bin/pip install -r requirements.txt; \
		touch $(VENV_MARKER); \
	fi

clean-venv:
	rm -rf $(VENV_DIR)

test: venv
	$(VENV_PYTHON) -m unittest discover -s tests -p "test_*.py"
