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
from controllers.comparison_controller import router as comparison_router
from controllers.notification_controller import router as notification_router
from controllers.user_controller import router as user_router
from controllers.search_controller import router as search_router
from controllers.security_controller import router as security_router
from controllers.analytics_controller import router as analytics_router
from controllers.integration_controller import router as integration_router
from controllers.performance_controller import router as performance_router
from controllers.ml_controller import router as ml_router
from services.db import get_database
from services.dependency_service import get_dependency_graph
from services.history_service import get_trend_data, get_comparison_data
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
app.include_router(comparison_router, prefix="/comparison", tags=["comparison"])
app.include_router(notification_router, prefix="/notifications", tags=["notifications"])
app.include_router(user_router, prefix="/users", tags=["users"])
app.include_router(search_router, prefix="/search", tags=["search"])
app.include_router(security_router, prefix="/security", tags=["security"])
app.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
app.include_router(integration_router, prefix="/integrations", tags=["integrations"])
app.include_router(performance_router, prefix="/performance", tags=["performance"])
app.include_router(ml_router, prefix="/ml", tags=["ml"])


# ============== Dependency Graph Endpoints ==============
@app.get("/dependencies/{project_id}", tags=["dependencies"])
async def get_dependencies(project_id: str):
    """Get dependency graph data for D3.js visualization."""
    try:
        graph = await get_dependency_graph(project_id)
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
        trends = await get_trend_data(project_id, days=30, limit=limit)
        return {"project_id": project_id, "scans": trends.get("scans", [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/{project_id}/trends", tags=["history"])
async def get_project_trends(project_id: str):
    """Get trend analysis for a project."""
    try:
        trends = await get_trend_data(project_id)
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/{project_id}/compare", tags=["history"])
async def compare_scans(project_id: str):
    """Compare current scan with previous."""
    try:
        comparison = await get_comparison_data(project_id)
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
