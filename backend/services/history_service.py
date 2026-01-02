"""
Historical Trends Service - Tracks scan history in MongoDB for comparisons and timeline analysis.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any


async def save_scan_snapshot(project_id: str, metrics: Dict[str, Any]) -> str:
    """Save a scan snapshot to the database."""
    from services.db import db
    
    snapshot = {
        "project_id": project_id,
        "scan_id": f"scan_{int(datetime.utcnow().timestamp())}",
        "timestamp": datetime.utcnow(),
        "metrics": metrics,
        "created_at": datetime.utcnow()
    }
    
    # Store in scan_history collection
    await db.insert("scan_history", snapshot)
    
    return snapshot["scan_id"]


async def get_scan_history(project_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get scan history for a project."""
    from services.db import db
    
    history = await db.find(
        "scan_history",
        {"project_id": project_id},
        sort=[("timestamp", -1)],
        limit=limit
    )
    
    return history


async def get_trend_data(project_id: str, days: int = 30, limit: int = 50) -> Dict[str, Any]:
    """Get historical trend data for a project."""
    from services.db import db
    
    # Get current metrics and smells
    metrics = await db.get_metrics(project_id)
    smells = await db.get_smells(project_id)
    risks = await db.get_risks(project_id)
    
    if not metrics:
        return {
            "project_id": project_id,
            "has_data": False,
            "message": "No data available. Analyze a repository first.",
            "current": None,
            "changes": None,
            "scans": []
        }
    
    # Calculate current summary
    total_files = len(metrics)
    total_smells = len(smells)
    
    # Calculate average risk
    avg_risk = 0
    if risks:
        avg_risk = sum(r.get("risk_score", 0) for r in risks) / len(risks)
    
    # Count issues by severity
    critical = sum(1 for s in smells if s.get("severity") == "critical")
    high = sum(1 for s in smells if s.get("severity") == "high")
    medium = sum(1 for s in smells if s.get("severity") == "medium")
    low = sum(1 for s in smells if s.get("severity") == "low" or not s.get("severity"))
    
    quality_score = max(0, 100 - avg_risk)
    
    current = {
        "total_files": total_files,
        "total_smells": total_smells,
        "quality_score": quality_score,
        "avg_risk": avg_risk,
        "critical_issues": critical,
        "high_issues": high,
        "medium_issues": medium,
        "low_issues": low
    }
    
    # Store in cache for history tracking
    if project_id not in _trends_cache:
        _trends_cache[project_id] = []
    
    # Add current snapshot to history
    snapshot = {
        "scan_id": f"scan_{len(_trends_cache[project_id]) + 1}",
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": current
    }
    
    # Only add if different from last snapshot
    if not _trends_cache[project_id] or _trends_cache[project_id][-1]["metrics"] != current:
        _trends_cache[project_id].append(snapshot)
    
    # Calculate changes (simulated for now)
    changes = {
        "quality_score": 0,
        "total_smells": 0,
        "avg_risk": 0
    }
    
    if len(_trends_cache[project_id]) >= 2:
        prev = _trends_cache[project_id][-2]["metrics"]
        if prev["quality_score"] > 0:
            changes["quality_score"] = ((current["quality_score"] - prev["quality_score"]) / prev["quality_score"]) * 100
        if prev["total_smells"] > 0:
            changes["total_smells"] = ((current["total_smells"] - prev["total_smells"]) / prev["total_smells"]) * 100
        if prev["avg_risk"] > 0:
            changes["avg_risk"] = ((current["avg_risk"] - prev["avg_risk"]) / prev["avg_risk"]) * 100
    
    return {
        "project_id": project_id,
        "has_data": True,
        "current": current,
        "changes": changes,
        "scans": _trends_cache[project_id][-limit:]
    }


async def get_comparison_data(project_id: str) -> Dict[str, Any]:
    """Compare current state with previous scan."""
    if project_id not in _trends_cache or len(_trends_cache[project_id]) < 2:
        return {
            "has_comparison": False,
            "message": "Not enough scans for comparison. Run more analyses."
        }
    
    current = _trends_cache[project_id][-1]
    previous = _trends_cache[project_id][-2]
    
    return {
        "has_comparison": True,
        "current": current,
        "previous": previous,
        "diff": {
            "quality_score": current["metrics"]["quality_score"] - previous["metrics"]["quality_score"],
            "total_smells": current["metrics"]["total_smells"] - previous["metrics"]["total_smells"],
            "files": current["metrics"]["total_files"] - previous["metrics"]["total_files"]
        }
    }
