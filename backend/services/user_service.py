"""
User Management Service
Handles user accounts, teams, and project sharing
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import hashlib
import secrets


class UserRole:
    OWNER = "owner"
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class UserService:
    """Manages users, teams, and access control"""
    
    def __init__(self, db):
        self.db = db
        self.users = {}
        self.teams = {}
        self.project_access = {}
        self.sessions = {}
    
    def hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = secrets.token_hex(32)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}${pwd_hash.hex()}"
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            salt, pwd_hash = hashed.split('$')
            new_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return new_hash.hex() == pwd_hash
        except:
            return False
    
    async def create_user(self, email: str, password: str, name: str, 
                         organization: Optional[str] = None) -> Dict:
        """Create a new user"""
        if email in self.users:
            raise ValueError("User already exists")
        
        user_id = f"user_{secrets.token_hex(8)}"
        user = {
            "id": user_id,
            "email": email,
            "password_hash": self.hash_password(password),
            "name": name,
            "organization": organization,
            "created_at": datetime.utcnow().isoformat(),
            "last_login": None,
            "active": True,
            "preferences": {
                "notifications": {
                    "email": True,
                    "slack": False,
                    "discord": False
                },
                "theme": "dark",
                "language": "en"
            }
        }
        
        self.users[email] = user
        return {"user_id": user_id, "email": email, "name": name}
    
    async def authenticate(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate user and create session"""
        user = self.users.get(email)
        if not user or not self.verify_password(password, user["password_hash"]):
            return None
        
        if not user["active"]:
            raise ValueError("User account is inactive")
        
        # Create session
        session_token = secrets.token_urlsafe(32)
        session = {
            "token": session_token,
            "user_id": user["id"],
            "email": email,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=7)
        }
        
        self.sessions[session_token] = session
        user["last_login"] = datetime.utcnow().isoformat()
        
        return {
            "session_token": session_token,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "organization": user["organization"]
            }
        }
    
    async def validate_session(self, session_token: str) -> Optional[Dict]:
        """Validate session token"""
        session = self.sessions.get(session_token)
        if not session:
            return None
        
        if datetime.utcnow() > session["expires_at"]:
            del self.sessions[session_token]
            return None
        
        return session
    
    async def logout(self, session_token: str):
        """Invalidate session"""
        if session_token in self.sessions:
            del self.sessions[session_token]
        return {"status": "logged_out"}
    
    async def create_team(self, name: str, owner_id: str, description: str = "") -> Dict:
        """Create a new team"""
        team_id = f"team_{secrets.token_hex(8)}"
        team = {
            "id": team_id,
            "name": name,
            "description": description,
            "owner_id": owner_id,
            "created_at": datetime.utcnow().isoformat(),
            "members": [
                {
                    "user_id": owner_id,
                    "role": UserRole.OWNER,
                    "joined_at": datetime.utcnow().isoformat()
                }
            ]
        }
        
        self.teams[team_id] = team
        return {"team_id": team_id, "name": name}
    
    async def add_team_member(self, team_id: str, user_id: str, role: str) -> Dict:
        """Add user to team"""
        team = self.teams.get(team_id)
        if not team:
            raise ValueError("Team not found")
        
        # Check if user already in team
        if any(m["user_id"] == user_id for m in team["members"]):
            raise ValueError("User already in team")
        
        team["members"].append({
            "user_id": user_id,
            "role": role,
            "joined_at": datetime.utcnow().isoformat()
        })
        
        return {"status": "member_added", "team_id": team_id, "user_id": user_id}
    
    async def remove_team_member(self, team_id: str, user_id: str) -> Dict:
        """Remove user from team"""
        team = self.teams.get(team_id)
        if not team:
            raise ValueError("Team not found")
        
        team["members"] = [m for m in team["members"] if m["user_id"] != user_id]
        return {"status": "member_removed"}
    
    async def share_project(self, project_id: str, user_id: str, 
                           shared_with: str, role: str) -> Dict:
        """Share project with another user"""
        if project_id not in self.project_access:
            self.project_access[project_id] = []
        
        # Check if already shared
        existing = next(
            (a for a in self.project_access[project_id] if a["user_id"] == shared_with),
            None
        )
        
        if existing:
            existing["role"] = role
            return {"status": "access_updated"}
        
        self.project_access[project_id].append({
            "user_id": shared_with,
            "role": role,
            "shared_by": user_id,
            "shared_at": datetime.utcnow().isoformat()
        })
        
        return {"status": "project_shared", "project_id": project_id}
    
    async def revoke_project_access(self, project_id: str, user_id: str) -> Dict:
        """Revoke project access"""
        if project_id in self.project_access:
            self.project_access[project_id] = [
                a for a in self.project_access[project_id]
                if a["user_id"] != user_id
            ]
        return {"status": "access_revoked"}
    
    async def get_user_projects(self, user_id: str) -> List[str]:
        """Get all projects accessible to user"""
        projects = []
        
        for project_id, access_list in self.project_access.items():
            if any(a["user_id"] == user_id for a in access_list):
                projects.append(project_id)
        
        return projects
    
    async def check_project_access(self, user_id: str, project_id: str) -> Optional[str]:
        """Check if user has access to project and return role"""
        access_list = self.project_access.get(project_id, [])
        access = next((a for a in access_list if a["user_id"] == user_id), None)
        
        return access["role"] if access else None
    
    async def get_team_members(self, team_id: str) -> List[Dict]:
        """Get all members of a team"""
        team = self.teams.get(team_id)
        if not team:
            raise ValueError("Team not found")
        
        return team["members"]
    
    async def update_user_preferences(self, user_id: str, preferences: Dict) -> Dict:
        """Update user preferences"""
        # Find user by ID
        user = next((u for u in self.users.values() if u["id"] == user_id), None)
        if not user:
            raise ValueError("User not found")
        
        user["preferences"].update(preferences)
        return {"status": "preferences_updated"}
