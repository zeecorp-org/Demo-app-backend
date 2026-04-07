FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "i=0; until alembic upgrade head; do i=$((i+1)); if [ \"$i\" -ge 20 ]; then echo 'Migration failed after 20 attempts'; exit 1; fi; echo 'Waiting for database before retrying migrations...'; sleep 2; done; exec uvicorn main:app --host 0.0.0.0 --port 8000"]

