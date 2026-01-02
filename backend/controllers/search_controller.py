"""
Search Controller
API endpoints for advanced search and filtering
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
from services.search_service import SearchService

router = APIRouter()


class FilterConditions(BaseModel):
    severity: Optional[List[str]] = None
    min_risk_score: Optional[float] = None
    max_risk_score: Optional[float] = None
    min_complexity: Optional[int] = None
    has_duplication: Optional[bool] = None
    file_types: Optional[List[str]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    min_issues: Optional[int] = None


class SaveFilterRequest(BaseModel):
    filter_name: str
    conditions: Dict


class SearchRequest(BaseModel):
    query: str
    filters: Optional[FilterConditions] = None


@router.post("/search/{project_id}")
async def search_files(project_id: str, request: SearchRequest):
    """
    Search files in project with advanced filtering
    
    Query can be: file name, code pattern, issue type, etc.
    Filters: severity, risk score, complexity, duplication, file types, dates
    """
    try:
        search_service = SearchService(None)
        
        filters_dict = request.filters.dict(exclude_none=True) if request.filters else None
        
        results = await search_service.search_files(
            project_id, request.query, filters_dict
        )
        
        return {
            "project_id": project_id,
            "query": request.query,
            "results_count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/{project_id}/quick")
async def quick_search(
    project_id: str,
    q: str = Query(..., description="Search query"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    min_risk: Optional[float] = Query(None, description="Minimum risk score")
):
    """Quick search with minimal filters"""
    try:
        search_service = SearchService(None)
        
        filters = {}
        if severity:
            filters['severity'] = [severity]
        if min_risk:
            filters['min_risk_score'] = min_risk
        
        results = await search_service.search_files(project_id, q, filters if filters else None)
        
        return {
            "query": q,
            "results_count": len(results),
            "results": results[:50]  # Limit to 50 results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/filters/save")
async def save_search_filter(user_id: str, request: SaveFilterRequest):
    """Save a custom search filter"""
    try:
        search_service = SearchService(None)
        result = await search_service.save_filter(
            user_id, request.filter_name, request.conditions
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/filters/{user_id}")
async def get_saved_filters(user_id: str):
    """Get all saved filters for a user"""
    try:
        search_service = SearchService(None)
        filters = await search_service.get_saved_filters(user_id)
        return {"filters": filters}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/search/filters/{user_id}/{filter_name}")
async def delete_search_filter(user_id: str, filter_name: str):
    """Delete a saved filter"""
    try:
        search_service = SearchService(None)
        result = await search_service.delete_filter(user_id, filter_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/{project_id}/apply-filter")
async def apply_saved_filter(
    project_id: str,
    user_id: str = Query(...),
    filter_name: str = Query(...),
    query: str = Query("")
):
    """Apply a saved filter to search"""
    try:
        search_service = SearchService(None)
        results = await search_service.apply_saved_filter(
            project_id, user_id, filter_name, query
        )
        return {
            "project_id": project_id,
            "filter_applied": filter_name,
            "results_count": len(results),
            "results": results
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/{project_id}/pattern")
async def pattern_search(
    project_id: str,
    pattern: str = Query(...),
    regex: bool = Query(False)
):
    """Search for code patterns using regex"""
    try:
        search_service = SearchService(None)
        results = await search_service.advanced_pattern_search(
            project_id, pattern, regex
        )
        return {
            "pattern": pattern,
            "regex_mode": regex,
            "results_count": len(results),
            "results": results
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/{project_id}/compare")
async def compare_files(project_id: str, file_paths: List[str]):
    """Compare multiple files side by side"""
    try:
        search_service = SearchService(None)
        comparison = await search_service.multi_file_comparison_search(
            project_id, file_paths
        )
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
