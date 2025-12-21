"""
Database Service for CodeSenseX

Supports both in-memory storage (for development) and MongoDB Atlas (for production).
Set USE_IN_MEMORY_DB=true in .env to use in-memory database.
"""

import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Check if we should use in-memory database
USE_IN_MEMORY = os.getenv("USE_IN_MEMORY_DB", "true").lower() == "true"


class DatabaseInterface(ABC):
    """Abstract interface for database operations."""
    
    @abstractmethod
    async def upsert_project(self, project: Dict[str, Any]) -> None:
        pass
    
    @abstractmethod
    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def set_metrics(self, project_id: str, metrics: List[Dict[str, Any]]) -> None:
        pass
    
    @abstractmethod
    async def get_metrics(self, project_id: str) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def set_risks(self, project_id: str, risks: List[Dict[str, Any]]) -> None:
        pass
    
    @abstractmethod
    async def get_risks(self, project_id: str) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def set_smells(self, project_id: str, smells: List[Dict[str, Any]]) -> None:
        pass
    
    @abstractmethod
    async def get_smells(self, project_id: str) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_scan_history(self, project_id: str, limit: int = 30) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_metrics_by_scan(self, project_id: str, scan_id: str) -> Optional[List[Dict[str, Any]]]:
        pass
    
    @abstractmethod
    async def get_smells_by_scan(self, project_id: str, scan_id: str) -> Optional[List[Dict[str, Any]]]:
        pass
    
    @abstractmethod
    async def save_scan_record(self, project_id: str, scan_data: Dict[str, Any]) -> str:
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        pass
    
    @abstractmethod
    async def close(self) -> None:
        pass


class InMemoryDB(DatabaseInterface):
    """In-memory database for development and testing."""
    
    def __init__(self):
        self.projects: Dict[str, Dict[str, Any]] = {}
        self.file_metrics: Dict[str, Dict[str, Any]] = {}
        self.risks: Dict[str, Dict[str, Any]] = {}
        self.smells: Dict[str, Dict[str, Any]] = {}
        self.scan_history: Dict[str, List[Dict[str, Any]]] = {}  # project_id -> list of scans
        self._connected = True
    
    async def upsert_project(self, project: Dict[str, Any]) -> None:
        self.projects[project["_id"]] = project
    
    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        return self.projects.get(project_id)
    
    async def set_metrics(self, project_id: str, metrics: List[Dict[str, Any]]) -> None:
        for m in metrics:
            key = f"{project_id}:{m.get('path', '')}"
            m['project_id'] = project_id
            self.file_metrics[key] = m
    
    async def get_metrics(self, project_id: str) -> List[Dict[str, Any]]:
        return [m for m in self.file_metrics.values() if m.get('project_id') == project_id]
    
    async def set_risks(self, project_id: str, risks: List[Dict[str, Any]]) -> None:
        for r in risks:
            key = f"{project_id}:{r.get('path', '')}"
            r['project_id'] = project_id
            self.risks[key] = r
    
    async def get_risks(self, project_id: str) -> List[Dict[str, Any]]:
        return [r for r in self.risks.values() if r.get('project_id') == project_id]
    
    async def set_smells(self, project_id: str, smells: List[Dict[str, Any]]) -> None:
        for s in smells:
            file_path = s.get("path", s.get("file_path", ""))
            key = f"{project_id}:{file_path}:{s.get('type', '')}:{s.get('line', 0)}"
            s['project_id'] = project_id
            self.smells[key] = s
    
    async def get_smells(self, project_id: str) -> List[Dict[str, Any]]:
        return [s for s in self.smells.values() if s.get('project_id') == project_id]
    
    async def get_scan_history(self, project_id: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Get historical scan records for a project."""
        return self.scan_history.get(project_id, [])[-limit:]
    
    async def get_metrics_by_scan(self, project_id: str, scan_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get metrics for a specific scan."""
        # In in-memory DB, return current metrics (no historical data stored separately)
        return await self.get_metrics(project_id)
    
    async def get_smells_by_scan(self, project_id: str, scan_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get issues for a specific scan."""
        # In in-memory DB, return current issues (no historical data stored separately)
        return await self.get_smells(project_id)
    
    async def save_scan_record(self, project_id: str, scan_data: Dict[str, Any]) -> str:
        """Save a scan record to history."""
        if project_id not in self.scan_history:
            self.scan_history[project_id] = []
        
        scan_data['_id'] = str(len(self.scan_history[project_id]))
        scan_data['timestamp'] = datetime.utcnow().isoformat()
        self.scan_history[project_id].append(scan_data)
        return scan_data['_id']
    
    async def connect(self) -> bool:
        print("✅ Using in-memory database")
        return True
    
    
    async def close(self) -> None:
        self.projects.clear()
        self.file_metrics.clear()
        self.risks.clear()
        self.smells.clear()
        print("🔌 In-memory database cleared")


class MongoDBAtlas(DatabaseInterface):
    """MongoDB Atlas database for production."""
    
    def __init__(self):
        self._client = None
        self._db = None
        self._connected = False
    
    async def connect(self) -> bool:
        """Connect to MongoDB Atlas."""
        if self._connected:
            return True
        
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            
            mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
            db_name = os.getenv("MONGODB_DB_NAME", "codesensex")
            max_pool = int(os.getenv("MONGO_MAX_POOL_SIZE", "10"))
            min_pool = int(os.getenv("MONGO_MIN_POOL_SIZE", "1"))
            
            self._client = AsyncIOMotorClient(
                mongo_uri,
                maxPoolSize=max_pool,
                minPoolSize=min_pool,
                serverSelectionTimeoutMS=5000
            )
            self._db = self._client[db_name]
            
            # Verify connection
            await self._client.admin.command('ping')
            self._connected = True
            print(f"✅ Connected to MongoDB Atlas: {db_name}")
            
            # Ensure indexes
            await self._ensure_indexes()
            
            return True
            
        except ImportError:
            print("⚠️  motor package not installed. Run: pip install motor")
            return False
        except Exception as e:
            print(f"⚠️  MongoDB connection failed: {e}")
            return False
    
    async def _ensure_indexes(self) -> None:
        """Create indexes for optimal query performance."""
        if self._db is None:
            return
        
        indexes = {
            "projects": [("name", 1)],
            "file_metrics": [("project_id", 1), ("path", 1)],
            "risks": [("project_id", 1), ("risk_score", -1)],
            "smells": [("project_id", 1), ("type", 1)]
        }
        
        for collection, keys in indexes.items():
            try:
                await self._db[collection].create_index(keys)
            except Exception as e:
                print(f"Warning: Could not create index on {collection}: {e}")
    
    async def close(self) -> None:
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            self._connected = False
            print("🔌 MongoDB connection closed")
    
    async def upsert_project(self, project: Dict[str, Any]) -> None:
        if not self._connected:
            await self.connect()
        await self._db.projects.update_one(
            {"_id": project["_id"]},
            {"$set": project},
            upsert=True
        )
    
    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        if not self._connected:
            await self.connect()
        return await self._db.projects.find_one({"_id": project_id})
    
    async def set_metrics(self, project_id: str, metrics: List[Dict[str, Any]]) -> None:
        if not self._connected:
            await self.connect()
        
        for m in metrics:
            m['project_id'] = project_id
            await self._db.file_metrics.update_one(
                {"project_id": project_id, "path": m.get("path", "")},
                {"$set": m},
                upsert=True
            )
    
    async def get_metrics(self, project_id: str) -> List[Dict[str, Any]]:
        if not self._connected:
            await self.connect()
        cursor = self._db.file_metrics.find({"project_id": project_id})
        results = await cursor.to_list(length=1000)
        # Convert ObjectId to string for JSON serialization
        for r in results:
            if '_id' in r:
                r['_id'] = str(r['_id'])
        return results
    
    async def set_risks(self, project_id: str, risks: List[Dict[str, Any]]) -> None:
        if not self._connected:
            await self.connect()
        
        for r in risks:
            r['project_id'] = project_id
            await self._db.risks.update_one(
                {"project_id": project_id, "path": r.get("path", "")},
                {"$set": r},
                upsert=True
            )
    
    async def get_risks(self, project_id: str) -> List[Dict[str, Any]]:
        if not self._connected:
            await self.connect()
        cursor = self._db.risks.find({"project_id": project_id}).sort("risk_score", -1)
        results = await cursor.to_list(length=1000)
        # Convert ObjectId to string for JSON serialization
        for r in results:
            if '_id' in r:
                r['_id'] = str(r['_id'])
        return results
    
    async def set_smells(self, project_id: str, smells: List[Dict[str, Any]]) -> None:
        if not self._connected:
            await self.connect()
        
        for s in smells:
            s['project_id'] = project_id
            file_path = s.get("path", s.get("file_path", ""))
            await self._db.smells.update_one(
                {"project_id": project_id, "path": file_path, "type": s.get("type", ""), "line": s.get("line", 0)},
                {"$set": s},
                upsert=True
            )
    
    async def get_smells(self, project_id: str) -> List[Dict[str, Any]]:
        if not self._connected:
            await self.connect()
        cursor = self._db.smells.find({"project_id": project_id})
        results = await cursor.to_list(length=1000)
        # Convert ObjectId to string for JSON serialization
        for r in results:
            if '_id' in r:
                r['_id'] = str(r['_id'])
        return results
    
    async def get_scan_history(self, project_id: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Get historical scan records for a project."""
        if not self._connected:
            await self.connect()
        cursor = self._db.scan_history.find({"project_id": project_id}).sort("timestamp", -1).limit(limit)
        results = await cursor.to_list(length=limit)
        for r in results:
            if '_id' in r:
                r['_id'] = str(r['_id'])
        return results
    
    async def get_metrics_by_scan(self, project_id: str, scan_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get metrics for a specific scan."""
        if not self._connected:
            await self.connect()
        cursor = self._db.file_metrics.find({"project_id": project_id, "scan_id": scan_id})
        results = await cursor.to_list(length=1000)
        for r in results:
            if '_id' in r:
                r['_id'] = str(r['_id'])
        return results if results else None
    
    async def get_smells_by_scan(self, project_id: str, scan_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get issues for a specific scan."""
        if not self._connected:
            await self.connect()
        cursor = self._db.smells.find({"project_id": project_id, "scan_id": scan_id})
        results = await cursor.to_list(length=1000)
        for r in results:
            if '_id' in r:
                r['_id'] = str(r['_id'])
        return results if results else None
    
    async def save_scan_record(self, project_id: str, scan_data: Dict[str, Any]) -> str:
        """Save a scan record to history."""
        if not self._connected:
            await self.connect()
        
        scan_data['project_id'] = project_id
        scan_data['timestamp'] = datetime.utcnow()
        
        result = await self._db.scan_history.insert_one(scan_data)
        return str(result.inserted_id)


# Singleton database instance
_db_instance: Optional[DatabaseInterface] = None

def get_database() -> DatabaseInterface:
    """Factory function to get the appropriate database instance (singleton)."""
    global _db_instance
    if _db_instance is None:
        if USE_IN_MEMORY:
            _db_instance = InMemoryDB()
        else:
            _db_instance = MongoDBAtlas()
    return _db_instance


# Global database instance for convenience
db = get_database()
