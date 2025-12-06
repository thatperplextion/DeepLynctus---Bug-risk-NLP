from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from controllers.upload_controller import router as upload_router
from controllers.scan_controller import router as scan_router
from controllers.metrics_controller import router as metrics_router
from controllers.risks_controller import router as risks_router
from controllers.smells_controller import router as smells_router
from controllers.suggestions_controller import router as suggestions_router
from controllers.report_controller import router as report_router
from services.db import get_database
from services.dependency_service import get_project_dependencies
from services.history_service import get_history, get_trends, get_comparison
from services.chatbot_service import chat_with_assistant, clear_chat_session


# Pydantic models for new endpoints
class ChatMessage(BaseModel):
    message: str
    file_context: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage database connection lifecycle."""
    db = get_database()
    # Startup: connect to database
    await db.connect()
    yield
    # Shutdown: close database connection
    await db.close()


app = FastAPI(
    title="Deep Lynctus Backend",
    version="0.2.0",
    description="AI-Powered Code Quality & Bug Risk Analyzer",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/upload", tags=["upload"])
app.include_router(scan_router, prefix="/scan", tags=["scan"])
app.include_router(metrics_router, prefix="/metrics", tags=["metrics"])
app.include_router(risks_router, prefix="/risks", tags=["risks"])
app.include_router(smells_router, prefix="/smells", tags=["smells"])
app.include_router(suggestions_router, prefix="/suggestions", tags=["suggestions"])
app.include_router(report_router, prefix="/report", tags=["report"])


# ============== Dependency Graph Endpoints ==============
@app.get("/dependencies/{project_id}", tags=["dependencies"])
async def get_dependencies(project_id: str):
    """Get dependency graph data for D3.js visualization."""
    try:
        graph = await get_project_dependencies(project_id)
        if not graph:
            raise HTTPException(status_code=404, detail="Project not found")
        return graph
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== History & Trends Endpoints ==============
@app.get("/history/{project_id}", tags=["history"])
async def get_scan_history(project_id: str, limit: int = 30):
    """Get scan history for a project."""
    try:
        history = await get_history(project_id, limit)
        return {"project_id": project_id, "scans": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/{project_id}/trends", tags=["history"])
async def get_project_trends(project_id: str):
    """Get trend analysis for a project."""
    try:
        trends = await get_trends(project_id)
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/{project_id}/compare", tags=["history"])
async def compare_scans(project_id: str, scan1: str, scan2: str):
    """Compare two scans."""
    try:
        comparison = await get_comparison(project_id, scan1, scan2)
        if not comparison:
            raise HTTPException(status_code=404, detail="Scans not found")
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== AI Chatbot Endpoints ==============
@app.post("/chat/{project_id}", tags=["chat"])
async def chat(project_id: str, chat_message: ChatMessage):
    """Chat with the AI code review assistant."""
    try:
        response = await chat_with_assistant(
            project_id, 
            chat_message.message, 
            chat_message.file_context
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/chat/{project_id}", tags=["chat"])
async def clear_chat(project_id: str):
    """Clear chat history for a project."""
    try:
        await clear_chat_session(project_id)
        return {"success": True, "message": "Chat history cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def root():
    return {"service": "deep-lynctus", "status": "ok"}
