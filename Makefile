.PHONY: setup demo dashboard test scrape analyze

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

setup:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

demo:
	$(PYTHON) -m src.main --demo

dashboard:
	$(PYTHON) -m src.dashboard.app

test:
	$(PYTHON) -m pytest src/tests/ -v

scrape:
	$(PYTHON) scraper/scrape_london.py

analyze:
	$(PYTHON) scraper/analyze.py
