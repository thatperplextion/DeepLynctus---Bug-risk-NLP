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
    
    # Save current snapshot to database
    await save_scan_snapshot(project_id, current)
    
    # Get historical scans from database
    history = await get_scan_history(project_id, limit)
    
    # Calculate changes compared to previous scan
    changes = {
        "quality_score": 0,
        "total_smells": 0,
        "avg_risk": 0,
        "critical_issues": 0,
        "high_issues": 0
    }
    
    if len(history) >= 2:
        prev = history[1]["metrics"]  # Second item is previous (first is current we just added)
        if prev.get("quality_score", 0) > 0:
            changes["quality_score"] = ((current["quality_score"] - prev["quality_score"]) / prev["quality_score"]) * 100
        if prev.get("total_smells", 0) > 0:
            changes["total_smells"] = ((current["total_smells"] - prev["total_smells"]) / prev["total_smells"]) * 100
        if prev.get("avg_risk", 0) > 0:
            changes["avg_risk"] = ((current["avg_risk"] - prev["avg_risk"]) / prev["avg_risk"]) * 100
        
        changes["critical_issues"] = current["critical_issues"] - prev.get("critical_issues", 0)
        changes["high_issues"] = current["high_issues"] - prev.get("high_issues", 0)
    
    return {
        "project_id": project_id,
        "has_data": True,
        "current": current,
        "changes": changes,
        "scans": [
            {
                "scan_id": h.get("scan_id"),
                "timestamp": h.get("timestamp").isoformat() if h.get("timestamp") else None,
                "metrics": h.get("metrics")
            }
            for h in history
        ]
    }


async def get_comparison_data(project_id: str) -> Dict[str, Any]:
    """Compare current state with previous scan."""
    history = await get_scan_history(project_id, limit=2)
    
    if len(history) < 2:
        return {
            "has_comparison": False,
            "message": "Not enough scans for comparison. Run more analyses."
        }
    
    current = history[0]  # Most recent
    previous = history[1]  # Previous scan
    
    curr_metrics = current.get("metrics", {})
    prev_metrics = previous.get("metrics", {})
    
    return {
        "has_comparison": True,
        "current": {
            "scan_id": current.get("scan_id"),
            "timestamp": current.get("timestamp").isoformat() if current.get("timestamp") else None,
            "metrics": curr_metrics
        },
        "previous": {
            "scan_id": previous.get("scan_id"),
            "timestamp": previous.get("timestamp").isoformat() if previous.get("timestamp") else None,
            "metrics": prev_metrics
        },
        "diff": {
            "quality_score": curr_metrics.get("quality_score", 0) - prev_metrics.get("quality_score", 0),
            "total_smells": curr_metrics.get("total_smells", 0) - prev_metrics.get("total_smells", 0),
            "files": curr_metrics.get("total_files", 0) - prev_metrics.get("total_files", 0),
            "critical_issues": curr_metrics.get("critical_issues", 0) - prev_metrics.get("critical_issues", 0),
            "high_issues": curr_metrics.get("high_issues", 0) - prev_metrics.get("high_issues", 0),
            "avg_risk": curr_metrics.get("avg_risk", 0) - prev_metrics.get("avg_risk", 0)
        },
        "percent_change": {
            "quality_score": ((curr_metrics.get("quality_score", 0) - prev_metrics.get("quality_score", 1)) / max(prev_metrics.get("quality_score", 1), 1)) * 100,
            "total_smells": ((curr_metrics.get("total_smells", 0) - prev_metrics.get("total_smells", 1)) / max(prev_metrics.get("total_smells", 1), 1)) * 100,
            "avg_risk": ((curr_metrics.get("avg_risk", 0) - prev_metrics.get("avg_risk", 1)) / max(prev_metrics.get("avg_risk", 1), 1)) * 100
        }
    }
