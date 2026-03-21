run:
	uvicorn main:app --reload

migrate:
	alembic upgrade head

revision:
	alembic revision --autogenerate -m "$(message)"

