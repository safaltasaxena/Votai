"""
backend/routers/ai.py — AI-specific endpoints like chat assist.
"""

from typing import Optional
from fastapi import APIRouter, Body
from pydantic import BaseModel
from services import ai_service

router = APIRouter(prefix="/ai", tags=["AI"])

class ChatRequest(BaseModel):
    message: str
    region_id: str
    language: str = "en"

@router.post("/chat")
async def chat_with_assistant(req: ChatRequest):
    """
    Controlled AI assistant for neutral party comparison and election help.
    """
    print("DEBUG ROUTER HIT:", req.message, req.region_id)
    result = ai_service.chat_assist(
        message=req.message,
        region_id=req.region_id,
        language=req.language
    )
    return result
