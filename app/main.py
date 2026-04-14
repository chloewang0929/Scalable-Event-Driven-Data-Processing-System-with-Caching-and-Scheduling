from fastapi import FastAPI
from app.api import endpoints
from app.db.session import engine, Base
import logging

# 初始化資料庫表格 (在現實應用中通常用 Alembic)
Base.metadata.create_all(bind=engine)

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Event Driven Data Processing System",
    description="A highly scalable event ingestion and processing REST API.",
    version="1.0.0"
)

# 註冊 Router
app.include_router(endpoints.router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "healthy"}
