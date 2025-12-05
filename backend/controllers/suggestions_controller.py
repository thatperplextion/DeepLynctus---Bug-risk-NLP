from fastapi import APIRouter
from services.llm_service import LLMService

router = APIRouter()

@router.get("/{project_id}/{file_id}")
async def get_suggestions(project_id: str, file_id: str, limit: int = 5):
    return await LLMService.fetch_suggestions(project_id, file_id, limit)
