# Demo-Umgebung Häuserhofer Haustechnik GmbH (Demo-Firma, fiktive Daten)
SHELL := /bin/bash
.DEFAULT_GOAL := help

-include .env
export

PYTHON   ?= python3
VENV     := .venv
PY       := $(VENV)/bin/python
DATA     := data/generated
SEED     ?= 2026
STICHTAG ?= $(shell date +%F)
COMPOSE  := docker compose
CHAT_MODEL      ?= gemma3:12b
EMBEDDING_MODEL ?= bge-m3

.PHONY: help check-env setup models data up down load reset test test-ki logs status clean

help: ## Diese Hilfe
	@grep -hE '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-9s %s\n", $$1, $$2}'

check-env:
	@test -f .env || { echo "FEHLER: .env fehlt. Anlegen mit: cp .env.example .env (und Werte prüfen)"; exit 1; }

$(VENV)/.ok: requirements.txt
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install -q --upgrade pip
	$(PY) -m pip install -q -r requirements.txt
	@touch $@

setup: check-env $(VENV)/.ok ## Python-Umgebung anlegen

models: ## Ollama-Modelle laden (Ollama läuft nativ auf macOS)
	@command -v ollama >/dev/null || { echo "FEHLER: ollama nicht installiert (https://ollama.com/download)"; exit 1; }
	ollama pull $(CHAT_MODEL)
	ollama pull $(EMBEDDING_MODEL)

data: $(VENV)/.ok ## Demo-Daten erzeugen (SEED=2026 STICHTAG=YYYY-MM-DD)
	$(PY) seed/generate.py --out $(DATA) --seed $(SEED) --stichtag $(STICHTAG)

up: check-env ## Dienste starten
	$(COMPOSE) up -d --wait

down: ## Dienste stoppen (Daten bleiben)
	$(COMPOSE) down

load: check-env $(VENV)/.ok ## Demo-Daten in die Dienste laden
	$(PY) seed/load.py --data $(DATA)

reset: check-env $(VENV)/.ok ## ALLES löschen, neu starten, Demo-Daten laden (vor jeder Aufnahme)
	$(COMPOSE) down -v --remove-orphans
	$(MAKE) data
	$(COMPOSE) up -d --wait
	$(MAKE) load

test: check-env $(VENV)/.ok ## Prüfen, ob alles bereit ist
	$(PY) scripts/test.py --data $(DATA)

test-ki: check-env $(VENV)/.ok ## Wie test, plus Demo-Fragen an das lokale Modell
	$(PY) scripts/test.py --data $(DATA) --ki

logs: ## Logs aller Dienste
	$(COMPOSE) logs -f --tail=100

status: ## Status der Dienste
	$(COMPOSE) ps

clean: ## Erzeugte Daten und Python-Umgebung löschen (Dienste bleiben)
	rm -rf $(DATA) $(VENV)
