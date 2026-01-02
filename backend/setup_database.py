"""
Setup MongoDB Collections and Indexes

This script creates all necessary collections and indexes in MongoDB Atlas
Run this to initialize your database schema
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("MONGODB_DB_NAME", "codesensex")


async def setup_database():
    """Create collections and indexes in MongoDB Atlas"""
    
    print(f"🔌 Connecting to MongoDB Atlas...")
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    
    try:
        # Test connection
        await client.admin.command('ping')
        print(f"✅ Connected to database: {DATABASE_NAME}\n")
        
        # 1. Projects Collection
        print("📁 Setting up 'projects' collection...")
        projects = db.projects
        try:
            await projects.create_index("project_id", unique=True)
        except Exception as e:
            if "already exists" in str(e) or "DuplicateKey" in str(e):
                print("   ℹ️  Index already exists, skipping...")
            else:
                raise
        try:
            await projects.create_index("created_at")
            await projects.create_index("user_id")
        except:
            pass
        print("✅ Projects collection ready")
        
        # 2. Files Collection
        print("📁 Setting up 'files' collection...")
        files = db.files
        await files.create_index([("project_id", 1), ("file_path", 1)], unique=True)
        await files.create_index([("project_id", 1), ("risk_score", -1)])
        await files.create_index([("project_id", 1), ("complexity", -1)])
        print("✅ Files collection ready")
        
        # 3. Risks Collection
        print("📁 Setting up 'risks' collection...")
        risks = db.risks
        await risks.create_index("project_id")
        await risks.create_index([("project_id", 1), ("severity", 1)])
        await risks.create_index("created_at")
        print("✅ Risks collection ready")
        
        # 4. Metrics Collection
        print("📁 Setting up 'metrics' collection...")
        metrics = db.metrics
        await metrics.create_index("project_id")
        await metrics.create_index("created_at")
        print("✅ Metrics collection ready")
        
        # 5. Users Collection (new)
        print("📁 Setting up 'users' collection...")
        users = db.users
        await users.create_index("email", unique=True)
        await users.create_index("user_id", unique=True)
        await users.create_index("organization")
        print("✅ Users collection ready")
        
        # 6. Teams Collection (new)
        print("📁 Setting up 'teams' collection...")
        teams = db.teams
        await teams.create_index("team_id", unique=True)
        await teams.create_index("owner_id")
        await teams.create_index("team_name")
        print("✅ Teams collection ready")
        
        # 7. Sessions Collection (new)
        print("📁 Setting up 'sessions' collection...")
        sessions = db.sessions
        await sessions.create_index("session_id", unique=True)
        await sessions.create_index("user_id")
        await sessions.create_index("expires_at", expireAfterSeconds=0)  # TTL index
        print("✅ Sessions collection ready")
        
        # 8. Notifications Collection (new)
        print("📁 Setting up 'notifications' collection...")
        notifications = db.notifications
        await notifications.create_index([("user_id", 1), ("created_at", -1)])
        await notifications.create_index([("user_id", 1), ("read", 1)])
        await notifications.create_index("project_id")
        print("✅ Notifications collection ready")
        
        # 9. Subscriptions Collection (new)
        print("📁 Setting up 'subscriptions' collection...")
        subscriptions = db.subscriptions
        await subscriptions.create_index([("user_id", 1), ("project_id", 1)], unique=True)
        await subscriptions.create_index("user_id")
        print("✅ Subscriptions collection ready")
        
        # 10. Saved Filters Collection (new)
        print("📁 Setting up 'saved_filters' collection...")
        saved_filters = db.saved_filters
        await saved_filters.create_index([("user_id", 1), ("filter_name", 1)])
        await saved_filters.create_index("user_id")
        print("✅ Saved filters collection ready")
        
        # 11. Security Scans Collection (new)
        print("📁 Setting up 'security_scans' collection...")
        security_scans = db.security_scans
        await security_scans.create_index("project_id")
        await security_scans.create_index([("project_id", 1), ("scan_date", -1)])
        print("✅ Security scans collection ready")
        
        # 12. Integrations Collection (new)
        print("📁 Setting up 'integrations' collection...")
        integrations = db.integrations
        await integrations.create_index([("project_id", 1), ("type", 1)], unique=True)
        await integrations.create_index("project_id")
        print("✅ Integrations collection ready")
        
        # 13. Cache Collection (new)
        print("📁 Setting up 'cache' collection...")
        cache = db.cache
        await cache.create_index("key", unique=True)
        await cache.create_index("expires_at", expireAfterSeconds=0)  # TTL index
        print("✅ Cache collection ready")
        
        # 14. File Hashes Collection (for incremental scans)
        print("📁 Setting up 'file_hashes' collection...")
        file_hashes = db.file_hashes
        await file_hashes.create_index([("project_id", 1), ("file_path", 1)], unique=True)
        await file_hashes.create_index("project_id")
        print("✅ File hashes collection ready")
        
        # 15. Migrations Collection (track migrations)
        print("📁 Setting up 'migrations' collection...")
        migrations = db.migrations
        await migrations.create_index("name", unique=True)
        await migrations.create_index("applied_at")
        print("✅ Migrations collection ready")
        
        # List all collections
        print("\n📋 Current collections in database:")
        collection_names = await db.list_collection_names()
        for name in sorted(collection_names):
            print(f"   • {name}")
        
        # Get database stats
        stats = await db.command("dbStats")
        print(f"\n📊 Database Statistics:")
        print(f"   • Collections: {stats['collections']}")
        print(f"   • Indexes: {stats['indexes']}")
        print(f"   • Data Size: {stats['dataSize'] / 1024:.2f} KB")
        
        print("\n✅ Database setup complete!")
        
    except Exception as e:
        print(f"\n❌ Error setting up database: {e}")
        raise
    finally:
        client.close()
        print("🔌 Connection closed")


if __name__ == "__main__":
    print("=" * 60)
    print("   MongoDB Atlas Database Setup")
    print("=" * 60)
    print()
    asyncio.run(setup_database())
