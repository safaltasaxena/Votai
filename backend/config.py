"""
config.py — Application settings and environment configuration.

Loads all external configuration from environment variables.
No hardcoded credentials or project-specific values here.
Uses python-dotenv to support a local .env file during development.
"""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load .env file if present (development only).
# In production (Cloud Run), env vars are injected directly.
load_dotenv()


@dataclass
class Settings:
    # ── Google Cloud ───────────────────────────────────────────────────────────
    # GCP project where Firestore and Vertex AI live.
    project_id: str = field(
        default_factory=lambda: os.environ["PROJECT_ID"]
    )

    # GCP region for Vertex AI endpoint (e.g. "us-central1", "asia-south1").
    region: str = field(
        default_factory=lambda: os.environ["REGION"]
    )

    # ── Firestore ──────────────────────────────────────────────────────────────
    # Use "(default)" unless a named database has been created.
    firestore_database: str = field(
        default_factory=lambda: os.getenv("FIRESTORE_DATABASE", "(default)")
    )

    # ── Application ────────────────────────────────────────────────────────────
    app_env: str = field(
        default_factory=lambda: os.getenv("APP_ENV", "development")
    )

    # Comma-separated list of allowed CORS origins.
    # Defaults to Vite dev server; override in production.
    cors_origins: list[str] = field(init=False)

    def __post_init__(self) -> None:
        raw = os.getenv("CORS_ORIGINS", "http://localhost:5173")
        self.cors_origins = [origin.strip() for origin in raw.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


# Single shared instance — import this wherever settings are needed.
settings = Settings()
