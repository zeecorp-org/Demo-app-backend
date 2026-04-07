run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

migrate:
	alembic upgrade head

revision:
	alembic revision --autogenerate -m "$(message)"

