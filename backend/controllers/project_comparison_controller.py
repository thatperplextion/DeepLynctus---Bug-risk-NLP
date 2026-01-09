"""
Project Comparison Controller - API endpoints for comparing two projects.
"""

from fastapi import APIRouter, HTTPException
from services.project_comparison_service import ProjectComparisonService
from services.db import get_database

router = APIRouter()


@router.get("/{project_a_id}/vs/{project_b_id}")
async def compare_two_projects(project_a_id: str, project_b_id: str):
    """
    Compare two projects side by side.
    
    Returns comprehensive comparison including:
    - Overall quality scores
    - Complexity comparison
    - Security issues
    - Code quality metrics
    - Winner determination
    """
    try:
        comparison = await ProjectComparisonService.compare_projects(project_a_id, project_b_id)
        
        if "error" in comparison:
            raise HTTPException(status_code=404, detail=comparison["error"])
        
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_all_projects():
    """
    Get list of all projects for comparison selection.
    """
    try:
        db = get_database()
        # Get all projects from database
        projects = []
        
        # For InMemoryDB
        if hasattr(db, 'projects'):
            projects = list(db.projects.values())
        # For MongoDB
        else:
            cursor = db._db["projects"].find({})
            projects = await cursor.to_list(length=1000)
            
        # Format for frontend
        project_list = [
            {
                "id": p.get("_id", ""),
                "name": p.get("name", "Unknown"),
                "repo_url": p.get("source_ref", ""),
                "status": p.get("status", "unknown"),
                "created_at": p.get("created_at", "")
            }
            for p in projects
        ]
        
        return {
            "projects": project_list,
            "count": len(project_list)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
