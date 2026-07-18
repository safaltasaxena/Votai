# backend/config.py

from dotenv import load_dotenv
import os
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv("backend/.env")


class Settings(BaseSettings):
    # Firestore
    project_id: str = os.getenv("PROJECT_ID", "votai-494905")
    firestore_database: str = os.getenv("FIRESTORE_DATABASE", "(default)")

    # App
    app_env: str = os.getenv("APP_ENV", "development")

    # Frontend CORS
    cors_origins: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173",
    )

    @property
    def cors_origins_list(self):
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()