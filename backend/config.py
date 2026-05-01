from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    PROJECT_ID: str = os.getenv("PROJECT_ID", "votai-494905")
    REGION: str = os.getenv("REGION", "us-central1")
    FIRESTORE_DATABASE: str = os.getenv("FIRESTORE_DATABASE", "(default)")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def cors_origins_list(self):
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

settings = Settings()