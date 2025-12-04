from fastapi import APIRouter
from pydantic import BaseModel
from services.job_service import JobService

router = APIRouter()

class ScanRequest(BaseModel):
    project_id: str
    options: dict | None = None

@router.post("/project")
async def scan_project(req: ScanRequest):
    started = await JobService.start_scan(req.project_id, req.options or {})
    return {"project_id": req.project_id, "status": "scanning", "started_at": started}
