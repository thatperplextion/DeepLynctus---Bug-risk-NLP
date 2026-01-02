#!/usr/bin/env python3
"""
Migration CLI Tool

Usage:
    python migrate.py status              # Show migration status
    python migrate.py up [target]         # Run migrations
    python migrate.py down [steps]        # Rollback migrations
"""

import sys
import asyncio
from backend.services.db import InMemoryDB
from backend.migrations.runner import MigrationRunner


async def main():
    # Initialize database
    db = InMemoryDB()
    runner = MigrationRunner(db)
    
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1]
    
    if command == "status":
        await runner.status()
    
    elif command == "up":
        target = sys.argv[2] if len(sys.argv) > 2 else None
        await runner.run_migrations(target)
    
    elif command == "down":
        steps = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        await runner.rollback(steps)
    
    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    asyncio.run(main())
