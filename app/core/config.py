from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Event Processing System"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/event_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # 測試覆蓋用
    TEST_DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5433/event_db_test"

    class Config:
        env_file = ".env"

settings = Settings()
