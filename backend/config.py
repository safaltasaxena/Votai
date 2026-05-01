from dotenv import load_dotenv
import os
from pydantic_settings import BaseSettings

# Force load .env from backend directory
load_dotenv("backend/.env")

class Settings(BaseSettings):
    project_id: str = os.getenv("PROJECT_ID", "votai-494905")
    firestore_database: str = os.getenv("FIRESTORE_DATABASE", "(default)")
    region: str = os.getenv("REGION", "us-central1")
    app_env: str = os.getenv("APP_ENV", "development")
    # Read raw string from environment
    cors_origins: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173"
    )

    @property
    def cors_origins_list(self):
        return [o.strip() for o in self.cors_origins.split(",")]

settings = Settings()
