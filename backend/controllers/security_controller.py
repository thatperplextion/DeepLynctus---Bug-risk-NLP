"""
Security Controller
API endpoints for security scanning
"""

from fastapi import APIRouter, HTTPException
from services.security_service import SecurityScanner

router = APIRouter()


@router.get("/security/{project_id}/secrets")
async def scan_secrets(project_id: str):
    """Scan for exposed secrets"""
    try:
        scanner = SecurityScanner(None)
        result = await scanner.scan_for_secrets(project_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/security/{project_id}/vulnerabilities")
async def scan_vulnerabilities(project_id: str):
    """Scan for OWASP vulnerabilities"""
    try:
        scanner = SecurityScanner(None)
        result = await scanner.scan_for_vulnerabilities(project_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/security/{project_id}/score")
async def get_security_score(project_id: str):
    """Get overall security score"""
    try:
        scanner = SecurityScanner(None)
        result = await scanner.calculate_security_score(project_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
