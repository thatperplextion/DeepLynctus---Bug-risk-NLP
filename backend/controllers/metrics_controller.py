from fastapi import APIRouter
from services.analytics_service import AnalyticsService

router = APIRouter()

@router.get("/{project_id}")
async def get_metrics(project_id: str, limit: int = 50, sort: str | None = None):
    return await AnalyticsService.fetch_metrics(project_id, limit, sort)
