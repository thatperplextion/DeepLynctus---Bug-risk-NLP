"""
Performance Controller  
API endpoints for performance optimization features
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from services.performance_service import PerformanceService

router = APIRouter()


class IncrementalScanRequest(BaseModel):
    files: List[str]


@router.post("/performance/{project_id}/incremental-scan")
async def incremental_scan(project_id: str, request: IncrementalScanRequest):
    """Perform incremental scan on changed files only"""
    try:
        service = PerformanceService(None)
        result = await service.incremental_scan(project_id, request.files)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/{project_id}/metrics-cached")
async def get_cached_metrics(project_id: str):
    """Get metrics with caching"""
    try:
        service = PerformanceService(None)
        result = await service.get_metrics_cached(project_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/performance/{project_id}/invalidate-cache")
async def invalidate_cache(project_id: str):
    """Invalidate cache for project"""
    try:
        service = PerformanceService(None)
        await service.invalidate_cache(project_id)
        return {"status": "cache_invalidated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/performance/batch-scan")
async def batch_scan(project_ids: List[str]):
    """Scan multiple projects in batch"""
    try:
        service = PerformanceService(None)
        result = await service.batch_scan_projects(project_ids)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
