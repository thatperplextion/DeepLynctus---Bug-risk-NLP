"""
Metrics Controller

Handles HTTP endpoints for retrieving and analyzing code metrics.
Provides file-level statistics including LOC, complexity, and quality indicators.
"""

import sys
import traceback
from fastapi import APIRouter, HTTPException

from services.analytics_service import AnalyticsService
from services.db import get_database

# Default pagination limit for metrics endpoints
DEFAULT_METRICS_LIMIT = 50

router = APIRouter()

@router.get("/{project_id}")
async def get_metrics(project_id: str, limit: int = DEFAULT_METRICS_LIMIT, sort: str | None = None):
    """
    Retrieve code metrics for a specific project.
    
    Args:
        project_id (str): Unique identifier of the project
        limit (int, optional): Maximum number of metrics to return. Defaults to 50.
        sort (str | None, optional): Sort field (e.g., 'complexity', 'loc'). Defaults to None.
    
    Returns:
        dict: Metrics data including file statistics and aggregated totals
        
    Raises:
        HTTPException: 500 if database error or processing fails
    """
    try:
        print(f"[DEBUG] get_metrics called for project: {project_id}", file=sys.stderr, flush=True)
        db = get_database()
        print(f"[DEBUG] DB instance: {type(db).__name__}, connected: {getattr(db, '_connected', 'N/A')}", file=sys.stderr, flush=True)
        result = await AnalyticsService.fetch_metrics(project_id, limit, sort)
        print(f"[DEBUG] Got {result.get('total', 0)} metrics", file=sys.stderr, flush=True)
        return result
    except Exception as e:
        print(f"[ERROR] Error fetching metrics: {e}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        raise HTTPException(status_code=500, detail=str(e))

