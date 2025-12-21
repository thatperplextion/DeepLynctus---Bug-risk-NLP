"""
Comparison Controller - API endpoints for scan comparison and regression detection.
"""

from fastapi import APIRouter, HTTPException
from services.comparison_service import ComparisonService

router = APIRouter()


@router.get("/{project_id}/history")
async def get_scan_history(project_id: str, limit: int = 30):
    """Get historical scans for a project."""
    try:
        scans = await ComparisonService.get_scan_history(project_id, limit)
        return {
            "project_id": project_id,
            "scans": scans,
            "count": len(scans)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/compare")
async def compare_two_scans(
    project_id: str,
    current_scan: str,
    previous_scan: str
):
    """
    Compare two scans and detect regressions.
    
    Query params:
    - current_scan: ID of the current scan
    - previous_scan: ID of the previous scan to compare against
    """
    try:
        comparison = await ComparisonService.compare_scans(
            project_id, current_scan, previous_scan
        )
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/timeline")
async def get_quality_timeline(project_id: str, days: int = 90):
    """
    Get code quality timeline over specified days.
    Shows quality score, issues count, etc. over time.
    """
    try:
        timeline = await ComparisonService.get_quality_timeline(project_id, days)
        return timeline
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/roi")
async def calculate_roi(project_id: str, days: int = 90):
    """
    Calculate ROI - measure improvement and estimate bug prevention cost savings.
    
    Query params:
    - days: Number of days to analyze (default: 90)
    """
    try:
        roi = await ComparisonService.calculate_roi(project_id, days)
        return roi
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
