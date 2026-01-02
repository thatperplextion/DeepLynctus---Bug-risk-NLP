"""
Analytics Controller
API endpoints for team analytics and dashboards
"""

from fastapi import APIRouter, HTTPException, Query
from services.team_analytics_service import TeamAnalyticsService

router = APIRouter()


@router.get("/analytics/{project_id}/productivity")
async def get_team_productivity(project_id: str, days: int = Query(30)):
    """Get team productivity metrics"""
    try:
        service = TeamAnalyticsService(None)
        result = await service.get_team_productivity(project_id, days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/{project_id}/cost-savings")
async def get_cost_savings(project_id: str, days: int = Query(30)):
    """Calculate cost savings from bug prevention"""
    try:
        service = TeamAnalyticsService(None)
        result = await service.calculate_cost_savings(project_id, days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/{project_id}/technology-heatmap")
async def get_technology_heatmap(project_id: str):
    """Get technology risk heatmap"""
    try:
        service = TeamAnalyticsService(None)
        result = await service.get_technology_heatmap(project_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
