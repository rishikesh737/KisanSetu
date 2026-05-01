# backend/api_gateway/main.py
from fastapi import FastAPI

app = FastAPI(title="KisanSetu API Gateway")


@app.get("/")
def read_root():
    return {"status": "healthy", "service": "KisanSetu API"}
