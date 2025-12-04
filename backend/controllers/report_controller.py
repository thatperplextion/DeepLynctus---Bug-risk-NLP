from fastapi import APIRouter, Response
from pydantic import BaseModel
from services.report_service import ReportService

router = APIRouter()

class ReportRequest(BaseModel):
    project_id: str
    format: str = "pdf"
    sections: list[str] | None = None

@router.post("/export")
async def export_report(req: ReportRequest):
    pdf_bytes = await ReportService.generate_pdf(req.project_id, req.sections or [])
    headers = {"Content-Disposition": f"attachment; filename=\"codesensex_{req.project_id}.pdf\""}
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
