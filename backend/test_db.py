"""
Database Connection Test Suite

Validates MongoDB Atlas connectivity and basic database operations.
Use this script to verify database setup before running the application.

Usage: python test_db.py
"""

import asyncio
import sys

# Add current directory to Python path for local imports
sys.path.insert(0, '.')

async def test():
    from services.db import get_database
    
    db = get_database()
    print(f"DB type: {type(db).__name__}")
    print(f"Connected: {getattr(db, '_connected', 'N/A')}")
    
    # Connect
    result = await db.connect()
    print(f"Connect result: {result}")
    
    # Try to get metrics
    project_id = "40846bcc-b2bd-4880-bc1a-b06a2beca718"
    try:
        metrics = await db.get_metrics(project_id)
        print(f"Metrics count: {len(metrics)}")
        if metrics:
            print(f"First metric: {metrics[0]}")
    except Exception as e:
        print(f"Error getting metrics: {e}")
        import traceback
        traceback.print_exc()
    
    # List all projects
    try:
        if hasattr(db, '_db'):
            cursor = db._db.projects.find({})
            projects = await cursor.to_list(length=100)
            print(f"\nProjects in DB: {len(projects)}")
            for p in projects:
                print(f"  - {p.get('_id')}: {p.get('source_ref', 'no url')}")
    except Exception as e:
        print(f"Error listing projects: {e}")

if __name__ == "__main__":
    asyncio.run(test())
