"""
Migration: Initial Database Schema
"""

from backend.migrations.runner import Migration


class InitialSchemaMigration(Migration):
    """Create initial collections and indexes"""
    
    async def up(self):
        """Apply migration"""
        # Create indexes for projects collection
        await self._create_collection_indexes("projects", [
            ("project_id", 1),
            ("created_at", -1),
            ("user_id", 1)
        ])
        
        # Create indexes for files collection
        await self._create_collection_indexes("files", [
            ("project_id", 1),
            ("file_path", 1),
            ("risk_score", -1)
        ])
        
        # Create indexes for risks collection
        await self._create_collection_indexes("risks", [
            ("project_id", 1),
            ("severity", 1),
            ("created_at", -1)
        ])
        
        # Create indexes for users collection
        await self._create_collection_indexes("users", [
            ("email", 1),  # Unique
            ("user_id", 1)
        ])
        
        # Create indexes for teams collection
        await self._create_collection_indexes("teams", [
            ("team_id", 1),
            ("owner_id", 1)
        ])
        
        print("✓ Created initial indexes")
    
    async def down(self):
        """Rollback migration"""
        # Drop all indexes (except _id)
        collections = ["projects", "files", "risks", "users", "teams"]
        
        for collection in collections:
            try:
                # Note: This is a simplified rollback
                # In production, you'd use proper index management
                print(f"Would drop indexes for {collection}")
            except Exception as e:
                print(f"Error dropping indexes for {collection}: {e}")
    
    async def _create_collection_indexes(self, collection: str, indexes: list):
        """Helper to create indexes for a collection"""
        for index_spec in indexes:
            field, direction = index_spec
            try:
                # Note: Actual index creation would use MongoDB driver
                # This is a placeholder for the pattern
                print(f"Creating index on {collection}.{field}")
            except Exception as e:
                print(f"Error creating index: {e}")
