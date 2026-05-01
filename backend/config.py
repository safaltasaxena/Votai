from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    project_id: str = os.getenv("PROJECT_ID", "votai-494905")
    region: str = os.getenv("REGION", "us-central1")
    firestore_database: str = os.getenv("FIRESTORE_DATABASE", "(default)")
    app_env: str = os.getenv("APP_ENV", "development")
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def cors_origins_list(self):
        return [o.strip() for o in self.cors_origins.split(",")]

settings = Settings()