# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
#print("CORS:", settings.cors_origins_list)
from routers import journey, elections, parties, ai

app = FastAPI(
    title="Votai API",
    description="AI Election Navigator Backend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(journey.router)
app.include_router(elections.router)
app.include_router(parties.router)
app.include_router(ai.router)


@app.get("/")
def root():
    return {"message": "Votai API is running 🚀"}


@app.get("/health")
def health():
    return {"status": "ok"}