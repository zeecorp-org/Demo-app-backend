# Demo App Backend Agent Guide

This file gives coding agents enough project context to make safe, consistent changes without first reverse-engineering the whole codebase.

## Project Purpose

This repository is a FastAPI backend scaffold with:

- versioned API routes
- SQLAlchemy ORM models and sessions
- Alembic migrations
- environment-driven configuration
- Docker and local development support

The app currently uses synchronous SQLAlchemy access and a production-style package layout under `app/`.

## High-Level Structure

### Entry Points

- `main.py`
  Thin import-only entrypoint for `uvicorn main:app`.
- `app/main.py`
  Real FastAPI application factory and app wiring.
  Add middleware, app-level lifecycle behavior, and top-level non-feature routes here.

### API Layer

- `app/api/router.py`
  Central router registry. Include feature routers here.
- `app/api/deps.py`
  Shared FastAPI dependencies, especially DB session injection.
- `app/api/v1/endpoints/`
  Versioned route handlers. Add one module per feature area when possible.

Put request/response handling in endpoint modules, but keep database logic out of them.

### Core Layer

- `app/core/config.py`
  Application settings and `.env` loading.
  Add new environment variables here.
- `app/core/logging.py`
  Logging configuration.
  Put global logging setup here, not inside feature modules.

### Database Layer

- `app/db/session.py`
  SQLAlchemy engine, session factory, and DB connectivity helpers.
- `app/db/base.py`
  Imports ORM models so Alembic autogenerate can discover them.

If you add a new model, make sure it is imported through `app/db/base.py`.

### Domain Models

- `app/models/base.py`
  Shared declarative base.
- `app/models/`
  SQLAlchemy ORM models. Create one file per entity or tightly related group.

Models define persistence structure, not API payload validation.

### Schemas

- `app/schemas/`
  Pydantic schemas for request and response models.

Use schemas for API input/output contracts. Do not expose ORM models directly from routes.

### CRUD / Data Access

- `app/crud/`
  Database access functions.

Put query and persistence logic here. Keep endpoint functions thin and focused on HTTP concerns.

### Migrations

- `alembic/env.py`
  Alembic runtime config, wired to app settings.
- `alembic/versions/`
  Migration files.

Whenever a model changes in a way that affects the database schema, create a migration.

## How To Add A New Feature

For a new resource or business area:

1. Add or update ORM models in `app/models/`.
2. Import those models in `app/db/base.py`.
3. Add request/response schemas in `app/schemas/`.
4. Add data access functions in `app/crud/`.
5. Add API endpoints in `app/api/v1/endpoints/`.
6. Register the router in `app/api/router.py`.
7. Generate and review an Alembic migration if schema changed.

Keep file names aligned by feature when possible, for example:

- `app/models/order.py`
- `app/schemas/order.py`
- `app/crud/order.py`
- `app/api/v1/endpoints/orders.py`

## Coding Rules For This Codebase

- Prefer small, focused changes that match the current architecture.
- Keep routes thin.
- Put SQLAlchemy queries in `app/crud`, not in route functions.
- Put validation for API payload shape in `app/schemas`.
- Put environment variables only in `app/core/config.py`.
- Keep the root `main.py` minimal.
- Reuse the existing synchronous DB session pattern unless explicitly refactoring to async across the project.
- Use type hints consistently.
- Follow existing response and error-handling style unless you are intentionally standardizing it across the app.

## What Goes Where

### Add a new env var

Update `app/core/config.py` and, if useful for developers, `.env.example`.

### Add middleware

Update `app/main.py`.

### Add a new router

Create the endpoint module under `app/api/v1/endpoints/` and register it in `app/api/router.py`.

### Add a new DB model

Create it in `app/models/`, then expose it in `app/db/base.py` so Alembic can see it.

### Add business query helpers

Put them in the appropriate `app/crud/*.py` file.

### Add request or response models

Put them in `app/schemas/*.py`.

### Change migration wiring

Update `alembic/env.py`, not application route modules.

## Change Safety Checklist

Before finishing a change:

- Make sure imports still resolve from `main.py`.
- Make sure new routes are registered.
- Make sure schema changes have Alembic migrations.
- Make sure new config values have sane defaults.
- Avoid hardcoding secrets, hosts, or DB URLs.
- Avoid creating duplicate logic across endpoints and CRUD modules.

## Local Workflow

Useful commands:

- `make run`
- `make migrate`
- `make revision message="describe_change"`
- `alembic upgrade head`
- `uvicorn main:app --reload`

## Agent Notes

- Respect the current project layout instead of introducing a second structure.
- If a change is cross-cutting, keep each layer responsible for its own concern.
- Prefer editing existing modules over creating one-off utility files without a clear home.
- If you add a new pattern, make it consistent enough that future features can follow it.
