"""
Analytics Service Module

Provides comprehensive analytics and metrics functionality for project analysis.
Handles data aggregation, metric calculation, and reporting for code quality insights.

This module processes project metrics including:
    - Code complexity metrics
    - Quality indicators
    - Performance statistics
    - Risk assessment data
"""

from .db import get_database
import traceback


class AnalyticsService:
    """
    Service for handling analytics and metrics operations.
    
    Provides methods for fetching, processing, and aggregating various metrics
    related to code quality, complexity, and risk assessment for projects.
    """
    @staticmethod
    async def fetch_metrics(project_id: str, limit: int, sort: str | None):
        try:
            db = get_database()
            # Ensure connected
            if hasattr(db, '_connected') and not db._connected:
                await db.connect()
            metrics = await db.get_metrics(project_id)
            # Parse sort parameter - expected format: "field_name:-1" or "field_name:1"
            if sort:
                try:
                    field, direction = sort.split(":")
                    # Convert direction string to boolean for reverse sorting
                    reverse = direction.strip() == "-1"
                    # Apply sorting to metrics based on specified field
                    metrics = sorted(metrics, key=lambda m: m.get(field, 0), reverse=reverse)
                except Exception:
                    # Silently ignore invalid sort parameters
                    pass
            
            # Return structured response with metrics and metadata
            return {
                "project_id": project_id,
                "metrics": metrics[:limit],  # Apply limit to results
                "total": len(metrics),       # Total count before limiting
                "updated_at": "now"          # Timestamp for cache invalidation
            }
        except Exception as e:
            print(f"Error in fetch_metrics: {e}")
            traceback.print_exc()
            raise

    @staticmethod
    async def fetch_risks(project_id: str, tier: str | None, top: int):
        try:
            db = get_database()
            if hasattr(db, '_connected') and not db._connected:
                await db.connect()
            items = await db.get_risks(project_id)
            if tier:
                items = [i for i in items if i.get("tier", "").lower() == tier.lower()]
            avg = round(sum(i.get("risk_score", 0) for i in items) / max(len(items), 1)) if items else 0
            high_count = sum(1 for i in items if i.get("tier") == "High")
            critical_count = sum(1 for i in items if i.get("tier") == "Critical")
            return {
                "project_id": project_id,
                "summary": {
                    "avg_risk": avg,
                    "high": high_count,
                    "critical": critical_count,
                    "total": len(items)
                },
                "items": sorted(items, key=lambda x: x.get("risk_score", 0), reverse=True)[:top]
            }
        except Exception as e:
            print(f"Error in fetch_risks: {e}")
            traceback.print_exc()
            raise

    @staticmethod
    async def fetch_smells(project_id: str, severity: int | None = None):
        try:
            db = get_database()
            if hasattr(db, '_connected') and not db._connected:
                await db.connect()
            smells = await db.get_smells(project_id)
            if severity is not None:
                smells = [s for s in smells if s.get("severity", 0) >= severity]
            
            # Group by type
            type_counts = {}
            for s in smells:
                t = s.get("type", "Unknown")
                type_counts[t] = type_counts.get(t, 0) + 1
            
            smell_types = [
                {"name": name, "count": count}
                for name, count in type_counts.items()
            ]
            
            # Get unique affected files (check both "path" and "file_path" for compatibility)
            affected_files = len(set(s.get("path", s.get("file_path", "")) for s in smells))
            
            return {
                "project_id": project_id,
                "total": len(smells),
                "affected_files": affected_files,
                "types": smell_types,
                "items": smells
            }
        except Exception as e:
            print(f"Error in fetch_smells: {e}")
            traceback.print_exc()
            raise
