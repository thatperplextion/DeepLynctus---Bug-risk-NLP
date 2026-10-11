# Database Persistence Update

## Overview
Updated the history service to use database persistence instead of in-memory cache, enabling timeline and comparison features to work across server restarts.

## Problem Statement
The original implementation used an in-memory cache (`_trends_cache`) to store historical scan data. This meant:
- All history was lost when the server restarted
- Comparison page always showed "Not enough scans" after restart
- Timeline page had no historical data to display
- Features were non-functional in production environment

## Solution
Migrated from in-memory cache to MongoDB-backed persistent storage using a `scan_history` collection.

## Changes Made

### 1. Database Interface (`backend/services/db.py`)

#### Added Generic Methods to DatabaseInterface
```python
@abstractmethod
async def find(self, collection: str, query: Dict[str, Any], sort: List = None, limit: int = None) -> List[Dict[str, Any]]:
    """Generic find method for any collection."""
    pass

@abstractmethod
async def insert(self, collection: str, document: Dict[str, Any]) -> str:
    """Generic insert method for any collection."""
    pass
```

#### InMemoryDB Implementation
- `find()`: Filters in-memory storage by query, applies sorting and limit
- `insert()`: Stores documents in appropriate internal dictionaries
- Special handling for `scan_history` collection which stores lists per project_id

#### MongoDBAtlas Implementation
- `find()`: Uses motor's async MongoDB queries with sorting and limits
- `insert()`: Uses motor's `insert_one()` operation
- Automatic ObjectId to string conversion for JSON serialization

### 2. History Service (`backend/services/history_service.py`)

#### New Functions

**`save_scan_snapshot()`**
```python
async def save_scan_snapshot(project_id: str, metrics: Dict[str, Any]) -> str:
    """Save a scan snapshot to the database."""
```
- Stores scan results in `scan_history` collection
- Generates unique scan_id with timestamp
- Returns scan_id for reference

**`get_scan_history()`**
```python
async def get_scan_history(project_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get scan history for a project."""
```
- Queries `scan_history` collection from MongoDB
- Sorts by timestamp descending (newest first)
- Applies limit to control result size

#### Rewritten Functions

**`get_trend_data()`**
- **Before**: Stored snapshots in `_trends_cache` dictionary
- **After**: Calls `save_scan_snapshot()` to persist to MongoDB
- Queries historical data using `get_scan_history()`
- Calculates changes by comparing current vs previous scan
- Returns formatted history from database

**`get_comparison_data()`**
- **Before**: Checked `_trends_cache` length, accessed list indices
- **After**: Queries database for last 2 scans
- Enhanced diff calculations including percent_change
- Returns comprehensive comparison metrics:
  - quality_score diff and percent change
  - total_smells diff and percent change
  - files, critical_issues, high_issues, avg_risk diffs
  - Timestamps for both scans

## Database Schema

### scan_history Collection
```json
{
  "_id": "ObjectId or auto-generated string",
  "project_id": "string - project identifier",
  "scan_id": "string - scan_{timestamp}",
  "timestamp": "datetime - when scan was performed",
  "created_at": "datetime - when record was created",
  "metrics": {
    "quality_score": "number",
    "total_smells": "number",
    "total_files": "number",
    "critical_issues": "number",
    "high_issues": "number",
    "medium_issues": "number",
    "low_issues": "number",
    "avg_risk": "number"
  }
}
```

## API Endpoints Affected

### GET `/api/trends/{project_id}`
- Now saves current scan to database on every call
- Returns historical data from database
- Shows changes compared to previous scan
- Includes list of all scans with timestamps

### GET `/api/comparison/{project_id}`
- Queries last 2 scans from database
- Returns detailed comparison with diff and percent_change
- Works after server restart (data persisted)

## Benefits

1. **Persistent History**: Scan data survives server restarts
2. **Scalable**: MongoDB handles large historical datasets efficiently
3. **Complete Timeline**: All scans stored with timestamps for trend analysis
4. **Working Comparisons**: Compare current state with any previous scan
5. **Production Ready**: No data loss in production environment
6. **Indexed Queries**: Fast retrieval with MongoDB indexes on project_id and timestamp

## Testing

### Verify Timeline Data
```bash
# Get trends for a project
curl http://localhost:8000/api/trends/{project_id}

# Should return:
# - current metrics
# - changes compared to previous scan
# - array of historical scans
```

### Verify Comparison Data
```bash
# Get comparison data
curl http://localhost:8000/api/comparison/{project_id}

# Should return:
# - current scan metrics
# - previous scan metrics
# - diff object with absolute changes
# - percent_change object with percentage changes
```

### Verify Persistence
1. Start backend and run a scan
2. Check that scan_history collection has data
3. Restart backend server
4. Call comparison endpoint - should still show previous scan data

## Database Collections

The application now uses these collections:
- `projects` - Project metadata
- `file_metrics` - File-level metrics per scan
- `risks` - Risk analysis results per file
- `smells` - Code smells detected per file
- **`scan_history`** - Historical scan snapshots (NEW)

## Migration Notes

- No migration required for existing data
- New scans will automatically populate scan_history
- Old projects will build history as new scans are performed
- First comparison requires at least 2 scans after update

## Configuration

No configuration changes required. The system automatically:
- Uses MongoDB when `USE_IN_MEMORY_DB=false` (default)
- Uses in-memory storage when `USE_IN_MEMORY_DB=true` (development)

## Status

✅ Database interface updated with generic methods
✅ InMemoryDB implementation complete
✅ MongoDBAtlas implementation complete
✅ History service refactored for database persistence
✅ Backend running successfully with MongoDB Atlas
✅ Ready for testing timeline and comparison pages
