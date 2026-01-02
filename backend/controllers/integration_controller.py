"""
Integration Controller
API endpoints for CI/CD and external integrations
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from services.integration_service import IntegrationService

router = APIRouter()


class GitHubIntegration(BaseModel):
    repo_url: str
    access_token: str


class GitLabIntegration(BaseModel):
    repo_url: str
    access_token: str


class JiraIntegration(BaseModel):
    jira_url: str
    project_key: str
    api_token: str


class WebhookIntegration(BaseModel):
    webhook_url: str
    events: List[str]


@router.post("/integrations/{project_id}/github")
async def setup_github(project_id: str, config: GitHubIntegration):
    """Setup GitHub Actions integration"""
    try:
        service = IntegrationService(None)
        result = await service.setup_github_integration(
            project_id, config.repo_url, config.access_token
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/integrations/{project_id}/gitlab")
async def setup_gitlab(project_id: str, config: GitLabIntegration):
    """Setup GitLab CI/CD integration"""
    try:
        service = IntegrationService(None)
        result = await service.setup_gitlab_integration(
            project_id, config.repo_url, config.access_token
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/integrations/{project_id}/jira")
async def setup_jira(project_id: str, config: JiraIntegration):
    """Setup Jira integration"""
    try:
        service = IntegrationService(None)
        result = await service.setup_jira_integration(
            project_id, config.jira_url, config.project_key, config.api_token
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/integrations/{project_id}/webhook")
async def setup_webhook(project_id: str, config: WebhookIntegration):
    """Setup webhook integration"""
    try:
        service = IntegrationService(None)
        result = await service.setup_webhook(
            project_id, config.webhook_url, config.events
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
