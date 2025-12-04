from fastapi import APIRouter
from services.analytics_service import AnalyticsService

router = APIRouter()

@router.get("/{project_id}")
async def get_risks(project_id: str, tier: str | None = None, top: int = 10):
    return await AnalyticsService.fetch_risks(project_id, tier, top)
