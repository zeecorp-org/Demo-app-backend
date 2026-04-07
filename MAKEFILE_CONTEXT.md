# Makefile Context For Local Routing Setup

This document explains the Make targets used to run the backend in WSL and OSRM in Docker for map routing.

## Goal

Provide a consistent, one-command-at-a-time setup path so teammates can clone the repository and start routing development quickly.

## Expected Runtime Model

- FastAPI backend runs directly in WSL
- OSRM runs in Docker
- Backend calls OSRM on localhost using environment configuration

## Prerequisites

- Ubuntu/WSL with Python 3
- Docker Engine installed and running in WSL
- Docker compose command available as docker-compose
- Optional but recommended: user in docker group

If Docker socket permission is not active in your current shell, Makefile OSRM targets automatically retry with sg docker.

## First-Time Setup From Fresh Clone

Run these commands in order:

    make setup-local
    make install-osmium
    make osrm-prepare
    make osrm-rebuild
    make osrm-health
    make run

## Daily Development Flow

Start routing stack:

    make osrm-up
    make run

Stop OSRM when done:

    make osrm-down

View OSRM logs:

    make osrm-logs

## Core Make Targets

### General

- make help
  - Shows a short command reference.

- make setup-local
  - Runs env-init and deps.

- make env-init
  - Creates .env from .env.example if missing.
  - Ensures osrm-data folder exists.

- make deps
  - Creates venv if missing.
  - Installs Python requirements.

### Backend

- make run
  - Starts FastAPI on 0.0.0.0:8000.

- make migrate
  - Applies Alembic migrations.

- make revision message="your_message"
  - Generates a migration revision.

### OSRM Lifecycle

- make osrm-up
  - Starts OSRM container.

- make osrm-down
  - Stops OSRM container.

- make osrm-logs
  - Follows OSRM logs.

- make osrm-reset-graph
  - Deletes generated region.osrm* artifacts.

- make osrm-rebuild
  - Runs osrm-down, osrm-reset-graph, then osrm-up.

### OSRM Data Preparation

- make osrm-download-karnataka
  - Downloads Karnataka source extract.
  - Copies it as active region.osm.pbf.

- make install-osmium
  - Installs osmium-tool using apt.

- make osrm-region-extract
  - Uses osmium to cut a smaller bbox region from the source extract.
  - Reduces memory pressure during OSRM graph build.

- make osrm-prepare
  - Runs env-init, osrm-download-karnataka, and osrm-region-extract.

### Routing Health Checks

- make osrm-health
  - Performs a lightweight route probe to confirm OSRM readiness.

- make routing-smoke
  - Executes a richer test query including geometry for manual inspection.

## Tunable Make Variables

These can be overridden at command time.

- PYTHON_BIN (default: python3)
- VENV_DIR (default: venv)
- OSRM_SOURCE_URL
- OSRM_SOURCE_FILE
- OSRM_REGION_FILE
- BBOX (default: 74.55,14.15,75.15,14.55)

Example override:

    make osrm-region-extract BBOX=74.0,13.8,75.6,15.0

## Troubleshooting

### Docker permission denied on /var/run/docker.sock

Run one of:

    newgrp docker

or reopen WSL terminal.

### OSRM build killed (Exit 137)

- This indicates memory pressure.
- Use a smaller regional extract via osrm-region-extract.
- Rebuild with make osrm-rebuild.

### Wrong-region routes

- Usually indicates wrong extract coverage.
- Regenerate region extract around your target area.
- Rebuild graph and retest.

## Ownership Notes For Team

- Keep source extract and generated region extract under osrm-data.
- Do not commit generated region.osrm* files.
- Share the same BBOX convention across teammates for consistent routing output.
