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
3. Run migrations with `alembic upgrade head`.
4. Start the API with `uvicorn main:app --reload`.

## Endpoints

- `/healthz`
- `/api/v1/health/live`
- `/api/v1/health/ready`
- `/api/v1/users`
- `/docs`
