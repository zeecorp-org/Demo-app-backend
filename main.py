from fastapi import FastAPI
from sqlalchemy import create_engine, text

app = FastAPI()

DATABASE_URL = "postgresql://demouser:demouser@localhost/testdb"

engine = create_engine(DATABASE_URL)


@app.get("/")
def read_root():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        return {"message": "DB Connected!", "result": [row[0] for row in result]}

