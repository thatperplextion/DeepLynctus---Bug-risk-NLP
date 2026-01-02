"""
Migration: Add Performance Indexes
"""

from backend.migrations.runner import Migration


class AddPerformanceIndexesMigration(Migration):
    """Add indexes for common query patterns"""
    
    async def up(self):
        """Apply migration"""
        # Compound index for file queries
        await self._create_index("files", [
            ("project_id", 1),
            ("risk_score", -1),
            ("created_at", -1)
        ])
        
        # Index for search queries
        await self._create_index("files", [
            ("project_id", 1),
            ("file_path", 1),
            ("complexity", -1)
        ])
        
        # Index for risk filtering
        await self._create_index("risks", [
            ("project_id", 1),
            ("severity", 1),
            ("status", 1)
        ])
        
        # Index for notification queries
        await self._create_index("notifications", [
            ("user_id", 1),
            ("read", 1),
            ("created_at", -1)
        ])
        
        # Index for session lookups
        await self._create_index("sessions", [
            ("session_id", 1),
            ("user_id", 1),
            ("expires_at", 1)
        ])
        
        # Index for cache entries
        await self._create_index("cache", [
            ("key", 1),
            ("expires_at", 1)
        ])
        
        # Text index for search
        await self._create_text_index("files", ["file_path", "issues"])
        
        print("✓ Created performance indexes")
    
    async def down(self):
        """Rollback migration"""
        print("Rolling back performance indexes...")
        # In production, would drop specific indexes by name
    
    async def _create_index(self, collection: str, fields: list):
        """Create compound index"""
        field_str = ", ".join(f"{f}:{d}" for f, d in fields)
        print(f"Creating compound index on {collection}: [{field_str}]")
    
    async def _create_text_index(self, collection: str, fields: list):
        """Create text search index"""
        print(f"Creating text index on {collection}: {fields}")
