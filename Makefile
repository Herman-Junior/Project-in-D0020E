.PHONY: run install help

PYTHON = venv/Scripts/python
BACKEND = Backend

help:
	@echo "Available commands:"
	@echo "  make install  - Install Python dependencies"
	@echo "  make run      - Start the Flask backend"

install:
	$(PYTHON) -m pip install -r $(BACKEND)/requirements.txt

run:
	cd $(BACKEND) && ../$(PYTHON) app.py
