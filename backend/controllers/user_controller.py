"""
User Management Controller
API endpoints for authentication and team management
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from services.user_service import UserService

router = APIRouter()


class UserRegistration(BaseModel):
    email: EmailStr
    password: str
    name: str
    organization: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TeamCreate(BaseModel):
    name: str
    description: str = ""


class TeamMemberAdd(BaseModel):
    user_id: str
    role: str  # owner, admin, developer, viewer


class ProjectShare(BaseModel):
    project_id: str
    shared_with: str
    role: str


class PreferencesUpdate(BaseModel):
    preferences: dict


@router.post("/auth/register")
async def register(user: UserRegistration):
    """Register a new user"""
    try:
        user_service = UserService(None)
        result = await user_service.create_user(
            user.email, user.password, user.name, user.organization
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/login")
async def login(credentials: UserLogin):
    """Authenticate user"""
    try:
        user_service = UserService(None)
        result = await user_service.authenticate(credentials.email, credentials.password)
        
        if not result:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/auth/logout")
async def logout(authorization: str = Header(None)):
    """Logout user"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    user_service = UserService(None)
    result = await user_service.logout(token)
    return result


@router.get("/auth/validate")
async def validate_session(authorization: str = Header(None)):
    """Validate session token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    user_service = UserService(None)
    session = await user_service.validate_session(token)
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    return {"valid": True, "user_id": session["user_id"]}


@router.post("/teams")
async def create_team(team: TeamCreate, authorization: str = Header(None)):
    """Create a new team"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    token = authorization.split(" ")[1]
    user_service = UserService(None)
    session = await user_service.validate_session(token)
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    result = await user_service.create_team(team.name, session["user_id"], team.description)
    return result


@router.post("/teams/{team_id}/members")
async def add_team_member(team_id: str, member: TeamMemberAdd, authorization: str = Header(None)):
    """Add member to team"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    user_service = UserService(None)
    result = await user_service.add_team_member(team_id, member.user_id, member.role)
    return result


@router.delete("/teams/{team_id}/members/{user_id}")
async def remove_team_member(team_id: str, user_id: str, authorization: str = Header(None)):
    """Remove member from team"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    user_service = UserService(None)
    result = await user_service.remove_team_member(team_id, user_id)
    return result


@router.get("/teams/{team_id}/members")
async def get_team_members(team_id: str, authorization: str = Header(None)):
    """Get all team members"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    user_service = UserService(None)
    members = await user_service.get_team_members(team_id)
    return {"members": members}


@router.post("/projects/share")
async def share_project(share: ProjectShare, authorization: str = Header(None)):
    """Share project with another user"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    token = authorization.split(" ")[1]
    user_service = UserService(None)
    session = await user_service.validate_session(token)
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    result = await user_service.share_project(
        share.project_id, session["user_id"], share.shared_with, share.role
    )
    return result


@router.delete("/projects/{project_id}/access/{user_id}")
async def revoke_access(project_id: str, user_id: str, authorization: str = Header(None)):
    """Revoke project access"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    user_service = UserService(None)
    result = await user_service.revoke_project_access(project_id, user_id)
    return result


@router.get("/users/projects")
async def get_user_projects(authorization: str = Header(None)):
    """Get all projects accessible to user"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    token = authorization.split(" ")[1]
    user_service = UserService(None)
    session = await user_service.validate_session(token)
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    projects = await user_service.get_user_projects(session["user_id"])
    return {"projects": projects}


@router.put("/users/preferences")
async def update_preferences(prefs: PreferencesUpdate, authorization: str = Header(None)):
    """Update user preferences"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    token = authorization.split(" ")[1]
    user_service = UserService(None)
    session = await user_service.validate_session(token)
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    result = await user_service.update_user_preferences(session["user_id"], prefs.preferences)
    return result
