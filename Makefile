DOCKER_COMPOSE := docker-compose
PYTHON_BIN ?= python3
VENV_DIR ?= venv

# Source extract used for Karnataka-first setup (fits local memory better than all-India).
OSRM_SOURCE_URL ?= https://download.openstreetmap.fr/extracts/asia/india/karnataka-latest.osm.pbf
OSRM_SOURCE_FILE ?= osrm-data/karnataka-full.osm.pbf
OSRM_REGION_FILE ?= osrm-data/region.osm.pbf

# Default bbox around Uttara Kannada area; override on command line when needed.
# Example:
# make osrm-region-extract BBOX=74.0,13.8,75.6,15.0
BBOX ?= 74.55,14.15,75.15,14.55

define COMPOSE_RUN
	@if docker info >/dev/null 2>&1; then \
		$(DOCKER_COMPOSE) $(1); \
	else \
		echo "Docker socket permission not active in this shell; using sg docker..."; \
		sg docker -c '$(DOCKER_COMPOSE) $(1)'; \
	fi
endef

.PHONY: help setup-local env-init deps run migrate revision \
	osrm-up osrm-logs osrm-down osrm-reset-graph \
	osrm-download-karnataka install-osmium osrm-region-extract \
	osrm-prepare osrm-rebuild osrm-health routing-smoke

help:
	@echo "Demo App Backend - Local Setup Commands"
	@echo ""
	@echo "  make setup-local            -> bootstrap .env + venv + dependencies"
	@echo "  make osrm-prepare           -> download Karnataka source + build reduced region extract"
	@echo "  make osrm-rebuild           -> remove graph files and start OSRM rebuild"
	@echo "  make osrm-health            -> OSRM readiness probe"
	@echo "  make routing-smoke          -> quick direct OSRM route check"
	@echo ""
	@echo "Common daily commands"
	@echo "  make run                    -> run FastAPI in WSL"
	@echo "  make osrm-up                -> start OSRM container"
	@echo "  make osrm-down              -> stop OSRM container"
	@echo "  make osrm-logs              -> stream OSRM logs"

setup-local: env-init deps
	@echo "Local backend setup complete."

env-init:
	@if [ ! -f .env ]; then cp .env.example .env; fi
	@mkdir -p osrm-data

deps:
	@if [ ! -d "$(VENV_DIR)" ]; then $(PYTHON_BIN) -m venv $(VENV_DIR); fi
	@. $(VENV_DIR)/bin/activate && pip install -r requirements.txt

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

migrate:
	alembic upgrade head

revision:
	alembic revision --autogenerate -m "$(message)"

osrm-up:
	$(call COMPOSE_RUN,up -d osrm)

osrm-logs:
	$(call COMPOSE_RUN,logs -f osrm)

osrm-down:
	$(call COMPOSE_RUN,stop osrm)

osrm-reset-graph:
	@rm -f osrm-data/region.osrm*

osrm-download-karnataka:
	@mkdir -p osrm-data
	@wget -O $(OSRM_SOURCE_FILE) $(OSRM_SOURCE_URL)
	@cp $(OSRM_SOURCE_FILE) $(OSRM_REGION_FILE)
	@ls -lh $(OSRM_SOURCE_FILE)

install-osmium:
	@sudo apt-get update && sudo apt-get install -y osmium-tool

osrm-region-extract:
	@if ! command -v osmium >/dev/null 2>&1; then \
		echo "osmium is required. Run: make install-osmium"; \
		exit 1; \
	fi
	@if [ ! -f "$(OSRM_SOURCE_FILE)" ]; then \
		echo "Missing $(OSRM_SOURCE_FILE). Run: make osrm-download-karnataka"; \
		exit 1; \
	fi
	@osmium extract --overwrite --bbox $(BBOX) --strategy=smart \
		-o $(OSRM_REGION_FILE) $(OSRM_SOURCE_FILE)
	@ls -lh $(OSRM_REGION_FILE)

osrm-prepare: env-init osrm-download-karnataka osrm-region-extract
	@echo "OSRM data prepared at $(OSRM_REGION_FILE)"

osrm-rebuild: osrm-down osrm-reset-graph osrm-up
	@echo "OSRM rebuild started. Use 'make osrm-logs' to monitor progress."

osrm-health:
	@curl -sS "http://127.0.0.1:5000/route/v1/driving/74.907045,14.33548075;74.896144,14.351798?overview=false&steps=false" | head -c 300 && echo

routing-smoke:
	@curl -sS "http://127.0.0.1:5000/route/v1/driving/74.907045,14.33548075;74.896144,14.351798?geometries=geojson&overview=full&steps=false" | head -c 1200 && echo

