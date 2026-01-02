"""
List MongoDB Collections and Indexes

Shows what's currently in your MongoDB Atlas database
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("MONGODB_DB_NAME", "codesensex")


async def list_database():
    """List all collections and indexes"""
    
    print(f"🔌 Connecting to MongoDB Atlas...")
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    
    try:
        # Test connection
        await client.admin.command('ping')
        print(f"✅ Connected to database: {DATABASE_NAME}\n")
        
        # List all collections
        collection_names = await db.list_collection_names()
        print(f"📋 Found {len(collection_names)} collections:\n")
        
        for name in sorted(collection_names):
            collection = db[name]
            
            # Count documents
            count = await collection.count_documents({})
            
            # List indexes
            indexes = await collection.list_indexes().to_list(length=100)
            index_names = [idx['name'] for idx in indexes if idx['name'] != '_id_']
            
            print(f"   📁 {name}")
            print(f"      Documents: {count}")
            if index_names:
                print(f"      Indexes: {', '.join(index_names)}")
            else:
                print(f"      Indexes: (none besides _id)")
            print()
        
        # Get database stats
        stats = await db.command("dbStats")
        print(f"📊 Database Statistics:")
        print(f"   • Total Collections: {stats['collections']}")
        print(f"   • Total Indexes: {stats['indexes']}")
        print(f"   • Data Size: {stats['dataSize'] / 1024:.2f} KB")
        print(f"   • Storage Size: {stats['storageSize'] / 1024:.2f} KB")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
    finally:
        client.close()
        print("\n🔌 Connection closed")


if __name__ == "__main__":
    print("=" * 60)
    print("   MongoDB Atlas Database Inspector")
    print("=" * 60)
    print()
    asyncio.run(list_database())
