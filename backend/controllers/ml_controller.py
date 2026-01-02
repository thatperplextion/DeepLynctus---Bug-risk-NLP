"""
ML Enhancement Controller
API endpoints for ML model explainability and enhancements
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from services.ml_enhancement_service import MLEnhancementService

router = APIRouter()


class ThresholdUpdate(BaseModel):
    risk_level: str
    threshold: float


@router.get("/ml/{project_id}/explain")
async def explain_risk_score(
    project_id: str,
    file_path: str = Query(...),
    risk_score: float = Query(...)
):
    """Explain why a file has a specific risk score"""
    try:
        service = MLEnhancementService(None)
        result = await service.explain_risk_score(file_path, risk_score)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ml/{project_id}/threshold")
async def set_threshold(project_id: str, request: ThresholdUpdate):
    """Set custom risk threshold"""
    try:
        service = MLEnhancementService(None)
        result = await service.set_custom_threshold(
            project_id, request.risk_level, request.threshold
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/{project_id}/anomalies")
async def detect_anomalies(project_id: str):
    """Detect code anomalies"""
    try:
        service = MLEnhancementService(None)
        result = await service.detect_anomalies(project_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ml/{project_id}/learn")
async def learn_from_history(project_id: str):
    """Learn patterns from historical data"""
    try:
        service = MLEnhancementService(None)
        result = await service.learn_from_history(project_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
