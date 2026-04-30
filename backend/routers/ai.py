from fastapi import APIRouter
from backend.services import ai_service

router = APIRouter(prefix="/ai", tags=["AI"])

@router.post("/chat")
async def chat(request: dict):
    print("DEBUG: Chat request received:", request)

    return ai_service.chat_assist(
        message=request.get("message"),
        region_id=request.get("region_id")
    )
