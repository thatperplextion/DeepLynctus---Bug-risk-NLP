from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel, HttpUrl
from services.repo_service import RepoService

router = APIRouter()

class UploadRequest(BaseModel):
    source_type: str  # 'github' | 'zip'
    source_ref: str   # URL or filename
    github_token: str | None = None

@router.post("/repo", status_code=202)
async def upload_repo(req: UploadRequest):
    project_id = await RepoService.queue_project(req)
    return {"project_id": project_id, "status": "queued"}

@router.post("/repo/file", status_code=202)
async def upload_zip(file: UploadFile = File(...)):
    project_id = await RepoService.queue_zip(file)
    return {"project_id": project_id, "status": "queued"}
