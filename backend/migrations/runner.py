"""
Database Migration System
"""

from typing import List, Dict, Any
from datetime import datetime
import os
import importlib.util


class Migration:
    """Base class for database migrations"""
    
    def __init__(self, db):
        self.db = db
    
    async def up(self):
        """Apply migration"""
        raise NotImplementedError("Migration must implement up() method")
    
    async def down(self):
        """Rollback migration"""
        raise NotImplementedError("Migration must implement down() method")


class MigrationRunner:
    """
    Database migration runner
    """
    
    def __init__(self, db, migrations_dir: str = "backend/migrations"):
        self.db = db
        self.migrations_dir = migrations_dir
        self.migrations_collection = "migrations"
    
    async def get_applied_migrations(self) -> List[str]:
        """Get list of applied migrations"""
        migrations = await self.db.find(
            self.migrations_collection,
            {}
        )
        return [m["name"] for m in migrations]
    
    async def get_pending_migrations(self) -> List[str]:
        """Get list of pending migrations"""
        applied = await self.get_applied_migrations()
        all_migrations = self._discover_migrations()
        return [m for m in all_migrations if m not in applied]
    
    def _discover_migrations(self) -> List[str]:
        """Discover all migration files"""
        if not os.path.exists(self.migrations_dir):
            return []
        
        migrations = []
        for filename in sorted(os.listdir(self.migrations_dir)):
            if filename.endswith(".py") and filename != "__init__.py" and filename != "runner.py":
                migrations.append(filename[:-3])  # Remove .py extension
        
        return migrations
    
    async def run_migrations(self, target: str = None):
        """
        Run pending migrations
        
        Args:
            target: Target migration name (run up to this migration)
        """
        pending = await self.get_pending_migrations()
        
        if target:
            # Run only up to target
            try:
                target_idx = pending.index(target)
                pending = pending[:target_idx + 1]
            except ValueError:
                print(f"Target migration {target} not found")
                return
        
        print(f"Running {len(pending)} migrations...")
        
        for migration_name in pending:
            print(f"Applying {migration_name}...")
            
            # Load migration module
            migration_class = self._load_migration(migration_name)
            migration = migration_class(self.db)
            
            # Run migration
            try:
                await migration.up()
                
                # Record migration
                await self.db.insert(
                    self.migrations_collection,
                    {
                        "name": migration_name,
                        "applied_at": datetime.utcnow()
                    }
                )
                
                print(f"✓ {migration_name} applied successfully")
            except Exception as e:
                print(f"✗ {migration_name} failed: {str(e)}")
                break
    
    async def rollback(self, steps: int = 1):
        """
        Rollback migrations
        
        Args:
            steps: Number of migrations to rollback
        """
        applied = await self.get_applied_migrations()
        
        if not applied:
            print("No migrations to rollback")
            return
        
        # Rollback last N migrations
        to_rollback = applied[-steps:]
        
        print(f"Rolling back {len(to_rollback)} migrations...")
        
        for migration_name in reversed(to_rollback):
            print(f"Rolling back {migration_name}...")
            
            # Load migration module
            migration_class = self._load_migration(migration_name)
            migration = migration_class(self.db)
            
            # Rollback migration
            try:
                await migration.down()
                
                # Remove migration record
                await self.db.delete(
                    self.migrations_collection,
                    {"name": migration_name}
                )
                
                print(f"✓ {migration_name} rolled back successfully")
            except Exception as e:
                print(f"✗ {migration_name} rollback failed: {str(e)}")
                break
    
    def _load_migration(self, migration_name: str):
        """Load migration class from file"""
        migration_path = os.path.join(self.migrations_dir, f"{migration_name}.py")
        
        spec = importlib.util.spec_from_file_location(migration_name, migration_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find Migration class
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, Migration) and attr != Migration:
                return attr
        
        raise ValueError(f"No Migration class found in {migration_name}")
    
    async def status(self):
        """Show migration status"""
        applied = await self.get_applied_migrations()
        pending = await self.get_pending_migrations()
        
        print("\n=== Migration Status ===")
        print(f"Applied: {len(applied)}")
        print(f"Pending: {len(pending)}")
        
        if applied:
            print("\nApplied migrations:")
            for m in applied:
                print(f"  ✓ {m}")
        
        if pending:
            print("\nPending migrations:")
            for m in pending:
                print(f"  ○ {m}")
