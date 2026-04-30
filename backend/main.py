# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.routers import journey, elections, parties

# ── App Initialization ───────────────────────────────────────────────────────

app = FastAPI(
    title="Votai API",
    description="AI Election Navigator Backend",
    version="1.0.0",
)

# ── CORS Setup ──────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Router Registration ─────────────────────────────────────────────────────

app.include_router(journey.router)
app.include_router(elections.router)
app.include_router(parties.router)

# ── Health Check ────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "Votai API is running 🚀"}

@app.get("/health")
def health():
    return {"status": "ok"}