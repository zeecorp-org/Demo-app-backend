# Demo App Backend

Production-ready FastAPI starter with:

- application factory structure
- environment-based configuration
- SQLAlchemy session management
- Alembic migrations
- health and readiness endpoints
- basic user CRUD
- Docker and Compose support

## Quick start

1. Create an environment file from `.env.example`.
2. Install dependencies with `pip install -r requirements.txt`.
3. Start Postgres. With Docker Compose, run `docker compose up -d db`.
4. Run migrations with `alembic upgrade head`, or rely on startup auto-creation in development.
5. Start the API with `uvicorn main:app --reload`.

## Database tables

This project defines two main tables:

- `users`
- `friendships`

If they do not appear in pgAdmin, first make sure you are connected to the same database as `DATABASE_URL`, which defaults to `postgresql://demouser:demouser@localhost/testdb`.

## Endpoints

- `/healthz`
- `/api/v1/health/live`
- `/api/v1/health/ready`
- `/api/v1/users`
- `/docs`
