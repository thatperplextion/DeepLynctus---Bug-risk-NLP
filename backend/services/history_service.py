"""
Historical Trends Service - Tracks and stores scan history for trend analysis.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict


async def save_scan_snapshot(project_id: str, scan_data: Dict[str, Any]) -> Dict[str, Any]:
    """Save a snapshot of scan results for historical tracking."""
    from services.db import db
    
    # Extract key metrics from scan data
    snapshot = {
        "project_id": project_id,
        "timestamp": datetime.utcnow(),
        "metrics": {
            "total_files": scan_data.get("files_analyzed", 0),
            "total_smells": scan_data.get("smells_found", 0),
            "quality_score": 100 - scan_data.get("summary", {}).get("avg_risk", 0),
            "critical_issues": scan_data.get("summary", {}).get("critical", 0),
            "high_issues": scan_data.get("summary", {}).get("high", 0),
            "medium_issues": scan_data.get("summary", {}).get("medium", 0),
            "low_issues": scan_data.get("summary", {}).get("low", 0),
        },
        "smell_breakdown": scan_data.get("smell_breakdown", {}),
        "language_stats": scan_data.get("language_stats", {}),
    }
    
    # Calculate additional metrics
    summary = scan_data.get("summary", {})
    snapshot["metrics"]["security_score"] = 100 - (summary.get("security_issues", 0) * 10)
    snapshot["metrics"]["maintainability_score"] = 100 - (summary.get("avg_complexity", 0) * 5)
    
    # Save to database
    result = await db.scan_history.insert_one(snapshot)
    snapshot["_id"] = str(result.inserted_id)
    
    return snapshot


async def get_trend_data(project_id: str, days: int = 30, limit: int = 50) -> Dict[str, Any]:
    """Get historical trend data for a project."""
    from services.db import db
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Query historical snapshots
    cursor = db.scan_history.find({
        "project_id": project_id,
        "timestamp": {"$gte": start_date, "$lte": end_date}
    }).sort("timestamp", 1).limit(limit)
    
    snapshots = await cursor.to_list(length=limit)
    
    if not snapshots:
        return {
            "project_id": project_id,
            "has_data": False,
            "message": "No historical data available. Run more scans to see trends.",
            "trends": [],
            "summary": None
        }
    
    # Format trend data for charts
    trends = []
    for snap in snapshots:
        trends.append({
            "date": snap["timestamp"].isoformat(),
            "quality_score": snap["metrics"].get("quality_score", 0),
            "total_issues": snap["metrics"].get("total_smells", 0),
            "critical": snap["metrics"].get("critical_issues", 0),
            "high": snap["metrics"].get("high_issues", 0),
            "files_analyzed": snap["metrics"].get("total_files", 0),
        })
    
    # Calculate trend direction
    if len(trends) >= 2:
        first = trends[0]
        last = trends[-1]
        quality_change = last["quality_score"] - first["quality_score"]
        issues_change = last["total_issues"] - first["total_issues"]
        
        trend_summary = {
            "quality_trend": "improving" if quality_change > 0 else "declining" if quality_change < 0 else "stable",
            "quality_change": round(quality_change, 1),
            "issues_trend": "improving" if issues_change < 0 else "declining" if issues_change > 0 else "stable",
            "issues_change": issues_change,
            "total_scans": len(trends),
            "first_scan": first["date"],
            "last_scan": last["date"],
            "avg_quality": round(sum(t["quality_score"] for t in trends) / len(trends), 1),
            "best_quality": max(t["quality_score"] for t in trends),
            "worst_quality": min(t["quality_score"] for t in trends),
        }
    else:
        trend_summary = {
            "quality_trend": "insufficient_data",
            "total_scans": len(trends),
            "message": "Need at least 2 scans for trend analysis"
        }
    
    return {
        "project_id": project_id,
        "has_data": True,
        "trends": trends,
        "summary": trend_summary,
        "period_days": days
    }


async def get_comparison_data(project_id: str) -> Dict[str, Any]:
    """Get comparison between latest scan and previous scans."""
    from services.db import db
    
    # Get last 2 scans
    cursor = db.scan_history.find({
        "project_id": project_id
    }).sort("timestamp", -1).limit(2)
    
    scans = await cursor.to_list(length=2)
    
    if len(scans) < 2:
        return {
            "has_comparison": False,
            "message": "Need at least 2 scans for comparison"
        }
    
    current = scans[0]["metrics"]
    previous = scans[1]["metrics"]
    
    # Calculate changes
    comparison = {
        "has_comparison": True,
        "current_scan": scans[0]["timestamp"].isoformat(),
        "previous_scan": scans[1]["timestamp"].isoformat(),
        "changes": {
            "quality_score": {
                "current": current.get("quality_score", 0),
                "previous": previous.get("quality_score", 0),
                "change": current.get("quality_score", 0) - previous.get("quality_score", 0),
                "improved": current.get("quality_score", 0) > previous.get("quality_score", 0)
            },
            "total_issues": {
                "current": current.get("total_smells", 0),
                "previous": previous.get("total_smells", 0),
                "change": current.get("total_smells", 0) - previous.get("total_smells", 0),
                "improved": current.get("total_smells", 0) < previous.get("total_smells", 0)
            },
            "critical_issues": {
                "current": current.get("critical_issues", 0),
                "previous": previous.get("critical_issues", 0),
                "change": current.get("critical_issues", 0) - previous.get("critical_issues", 0),
                "improved": current.get("critical_issues", 0) < previous.get("critical_issues", 0)
            },
            "files_analyzed": {
                "current": current.get("total_files", 0),
                "previous": previous.get("total_files", 0),
                "change": current.get("total_files", 0) - previous.get("total_files", 0)
            }
        }
    }
    
    # Overall assessment
    improvements = sum(1 for k, v in comparison["changes"].items() if isinstance(v, dict) and v.get("improved"))
    comparison["overall"] = "improving" if improvements >= 2 else "needs_attention"
    
    return comparison


async def get_smell_trends(project_id: str, days: int = 30) -> Dict[str, Any]:
    """Get trends for specific smell types over time."""
    from services.db import db
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    cursor = db.scan_history.find({
        "project_id": project_id,
        "timestamp": {"$gte": start_date}
    }).sort("timestamp", 1)
    
    snapshots = await cursor.to_list(length=100)
    
    if not snapshots:
        return {"has_data": False, "smell_trends": {}}
    
    # Aggregate smell data by type
    smell_trends = defaultdict(list)
    
    for snap in snapshots:
        timestamp = snap["timestamp"].isoformat()
        breakdown = snap.get("smell_breakdown", {})
        
        for smell_type, count in breakdown.items():
            smell_trends[smell_type].append({
                "date": timestamp,
                "count": count
            })
    
    return {
        "has_data": True,
        "smell_trends": dict(smell_trends),
        "period_days": days
    }
