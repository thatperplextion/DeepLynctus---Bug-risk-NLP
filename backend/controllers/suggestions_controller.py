from fastapi import APIRouter
from services.llm_service import LLMService

router = APIRouter()

@router.get("/{file_id}")
async def get_suggestions(file_id: str, limit: int = 5):
    return await LLMService.fetch_suggestions(file_id, limit)
