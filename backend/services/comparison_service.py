"""
Comparison Service - Compare code quality across scans and detect regressions.
Provides diff analysis, regression detection, and ROI tracking.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from services.db import get_database


class ComparisonService:
    """Service for comparing scans and detecting regressions."""
    
    @staticmethod
    async def get_scan_history(project_id: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Get list of historical scans for a project."""
        db = get_database()
        
        # Get all scan records for this project
        scans = await db.get_scan_history(project_id, limit=limit)
        
        return sorted(scans, key=lambda x: x.get("timestamp", 0), reverse=True)
    
    @staticmethod
    async def compare_scans(
        project_id: str, 
        scan_id_current: str, 
        scan_id_previous: str
    ) -> Dict[str, Any]:
        """
        Compare two scans and detect regressions.
        
        Returns:
            Dictionary with:
            - metrics_diff: Changes in metrics
            - regressions: New issues found
            - improvements: Issues fixed
            - files_changed: Files with quality changes
            - risk_delta: Change in overall risk
        """
        db = get_database()
        
        # Get metrics from both scans
        current_metrics = await db.get_metrics_by_scan(project_id, scan_id_current) or []
        previous_metrics = await db.get_metrics_by_scan(project_id, scan_id_previous) or []
        
        # Get issues from both scans
        current_issues = await db.get_smells_by_scan(project_id, scan_id_current) or []
        previous_issues = await db.get_smells_by_scan(project_id, scan_id_previous) or []
        
        # Build file maps for comparison
        current_file_map = {m.get("path"): m for m in current_metrics}
        previous_file_map = {m.get("path"): m for m in previous_metrics}
        
        current_issue_keys = {(i.get("path"), i.get("type"), i.get("message")[:50]) 
                             for i in current_issues}
        previous_issue_keys = {(i.get("path"), i.get("type"), i.get("message")[:50]) 
                              for i in previous_issues}
        
        # Calculate differences
        new_issues = current_issue_keys - previous_issue_keys
        fixed_issues = previous_issue_keys - current_issue_keys
        
        # Find files with changed metrics
        files_changed = []
        for file_path in set(list(current_file_map.keys()) + list(previous_file_map.keys())):
            current_file = current_file_map.get(file_path)
            previous_file = previous_file_map.get(file_path)
            
            if current_file and previous_file:
                current_risk = current_file.get("risk_score", 0)
                previous_risk = previous_file.get("risk_score", 0)
                risk_change = current_risk - previous_risk
                
                if abs(risk_change) > 0:
                    files_changed.append({
                        "path": file_path,
                        "risk_change": risk_change,
                        "current_risk": current_risk,
                        "previous_risk": previous_risk,
                        "status": "regressed" if risk_change > 0 else "improved",
                        "current_metrics": current_file,
                        "previous_metrics": previous_file
                    })
        
        # Sort by impact
        files_changed.sort(key=lambda x: abs(x["risk_change"]), reverse=True)
        
        # Calculate overall metrics
        current_avg_risk = sum(m.get("risk_score", 0) for m in current_metrics) / len(current_metrics) if current_metrics else 0
        previous_avg_risk = sum(m.get("risk_score", 0) for m in previous_metrics) / len(previous_metrics) if previous_metrics else 0
        
        critical_current = sum(1 for i in current_issues if i.get("severity", "").lower() == "critical")
        critical_previous = sum(1 for i in previous_issues if i.get("severity", "").lower() == "critical")
        high_current = sum(1 for i in current_issues if i.get("severity", "").lower() == "high")
        high_previous = sum(1 for i in previous_issues if i.get("severity", "").lower() == "high")
        
        return {
            "scan_current": scan_id_current,
            "scan_previous": scan_id_previous,
            "metrics": {
                "avg_risk_change": current_avg_risk - previous_avg_risk,
                "current_avg_risk": current_avg_risk,
                "previous_avg_risk": previous_avg_risk,
                "files_analyzed_current": len(current_metrics),
                "files_analyzed_previous": len(previous_metrics),
                "files_with_changes": len(files_changed)
            },
            "regressions": {
                "new_issues": len(new_issues),
                "critical_change": critical_current - critical_previous,
                "high_change": high_current - high_previous,
                "new_critical_issues": sum(1 for k in new_issues 
                                           for i in current_issues 
                                           if i.get("severity", "").lower() == "critical" 
                                           and (i.get("path"), i.get("type"), i.get("message")[:50]) == k)
            },
            "improvements": {
                "fixed_issues": len(fixed_issues),
                "critical_fixed": sum(1 for k in fixed_issues 
                                       for i in previous_issues 
                                       if i.get("severity", "").lower() == "critical" 
                                       and (i.get("path"), i.get("type"), i.get("message")[:50]) == k)
            },
            "files_changed": files_changed[:10],  # Top 10 changed files
            "new_issues_sample": list(new_issues)[:5],
            "fixed_issues_sample": list(fixed_issues)[:5],
            "health_status": ComparisonService._get_health_status(
                critical_current, high_current, 
                critical_previous, high_previous,
                current_avg_risk, previous_avg_risk
            )
        }
    
    @staticmethod
    def _get_health_status(critical_cur, high_cur, critical_prev, high_prev, 
                          risk_cur, risk_prev) -> Dict[str, Any]:
        """Determine health status of the project."""
        has_critical = critical_cur > 0
        has_high = high_cur > 0
        risk_worse = risk_cur > risk_prev
        
        if has_critical:
            return {
                "status": "critical",
                "message": f"🔴 {critical_cur} CRITICAL issues detected",
                "color": "red"
            }
        elif has_high:
            return {
                "status": "warning",
                "message": f"🟠 {high_cur} high-priority issues",
                "color": "orange"
            }
        elif risk_worse:
            return {
                "status": "regressed",
                "message": f"📈 Code quality decreased by {risk_cur - risk_prev:.1f}%",
                "color": "yellow"
            }
        else:
            return {
                "status": "healthy",
                "message": "✅ Code quality is healthy",
                "color": "green"
            }
    
    @staticmethod
    async def get_quality_timeline(project_id: str, days: int = 90) -> Dict[str, Any]:
        """
        Get code quality metrics over time.
        
        Returns timeline data showing quality score, issues count, etc.
        """
        db = get_database()
        
        # Get historical scan data
        scans = await db.get_scan_history(project_id, limit=100)
        
        # Filter by date range
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        scans = [s for s in scans if datetime.fromisoformat(s.get("timestamp", "")) > cutoff_date]
        
        timeline_data = []
        for scan in sorted(scans, key=lambda x: x.get("timestamp", "")):
            metrics = await db.get_metrics_by_scan(project_id, scan.get("_id", "")) or []
            issues = await db.get_smells_by_scan(project_id, scan.get("_id", "")) or []
            
            avg_risk = sum(m.get("risk_score", 0) for m in metrics) / len(metrics) if metrics else 0
            quality_score = 100 - avg_risk
            
            timeline_data.append({
                "scan_id": scan.get("_id"),
                "timestamp": scan.get("timestamp"),
                "quality_score": quality_score,
                "avg_risk": avg_risk,
                "total_issues": len(issues),
                "critical_issues": sum(1 for i in issues if i.get("severity", "").lower() == "critical"),
                "high_issues": sum(1 for i in issues if i.get("severity", "").lower() == "high"),
                "files_analyzed": len(metrics)
            })
        
        return {
            "project_id": project_id,
            "days": days,
            "timeline": timeline_data,
            "summary": ComparisonService._calculate_timeline_summary(timeline_data)
        }
    
    @staticmethod
    def _calculate_timeline_summary(timeline_data: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics from timeline data."""
        if not timeline_data:
            return {}
        
        latest = timeline_data[-1] if timeline_data else {}
        oldest = timeline_data[0] if timeline_data else {}
        
        quality_trend = latest.get("quality_score", 0) - oldest.get("quality_score", 0)
        issues_trend = latest.get("total_issues", 0) - oldest.get("total_issues", 0)
        
        max_quality = max((d.get("quality_score", 0) for d in timeline_data), default=0)
        min_quality = min((d.get("quality_score", 0) for d in timeline_data), default=0)
        
        return {
            "current_quality": latest.get("quality_score", 0),
            "quality_trend": quality_trend,
            "trend_direction": "up" if quality_trend > 0 else "down" if quality_trend < 0 else "stable",
            "quality_range": {"max": max_quality, "min": min_quality},
            "current_issues": latest.get("total_issues", 0),
            "issues_trend": issues_trend,
            "improvement_potential": min_quality - max_quality  # How much improved
        }
    
    @staticmethod
    async def calculate_roi(project_id: str, days: int = 90) -> Dict[str, Any]:
        """
        Calculate ROI - measure improvement and estimate bug prevention.
        
        Returns:
            ROI metrics including:
            - Issues fixed
            - Estimated cost savings (based on bug prevention)
            - Quality improvement percentage
            - Files improved
        """
        timeline = await ComparisonService.get_quality_timeline(project_id, days)
        timeline_data = timeline.get("timeline", [])
        
        if len(timeline_data) < 2:
            return {
                "status": "insufficient_data",
                "message": "Need at least 2 scans to calculate ROI"
            }
        
        first_scan = timeline_data[0]
        last_scan = timeline_data[-1]
        
        # Calculate improvements
        issues_fixed = first_scan.get("total_issues", 0) - last_scan.get("total_issues", 0)
        quality_improvement = last_scan.get("quality_score", 0) - first_scan.get("quality_score", 0)
        critical_fixed = first_scan.get("critical_issues", 0) - last_scan.get("critical_issues", 0)
        
        # Estimate cost savings (industry average: $100-$500 per bug in production)
        # Using conservative $150 per critical bug, $50 per high-priority bug
        avg_cost_per_critical = 300
        avg_cost_per_bug = 75
        
        critical_savings = critical_fixed * avg_cost_per_critical
        total_bug_savings = issues_fixed * avg_cost_per_bug
        total_savings = critical_savings + total_bug_savings
        
        # Calculate developer hours saved (5 mins per minor issue, 30 mins per critical)
        hours_saved = (critical_fixed * 0.5) + (issues_fixed * 0.083)
        
        return {
            "period_days": days,
            "improvements": {
                "issues_fixed": issues_fixed,
                "critical_issues_fixed": critical_fixed,
                "quality_improvement_percent": quality_improvement,
                "quality_score_current": last_scan.get("quality_score", 0),
                "quality_score_previous": first_scan.get("quality_score", 0),
                "files_scanned": last_scan.get("files_analyzed", 0)
            },
            "roi_metrics": {
                "estimated_cost_savings": f"${total_savings:,.0f}",
                "developer_hours_saved": f"{hours_saved:.1f}",
                "bugs_prevented": issues_fixed,
                "time_period_days": days
            },
            "roi_score": ComparisonService._calculate_roi_score(
                issues_fixed, quality_improvement, critical_fixed
            )
        }
    
    @staticmethod
    def _calculate_roi_score(issues_fixed: int, quality_improvement: float, 
                            critical_fixed: int) -> str:
        """Calculate ROI effectiveness score."""
        score = 0
        
        # Points for issues fixed
        score += min(issues_fixed * 2, 30)
        
        # Points for quality improvement
        score += min(quality_improvement * 2, 30)
        
        # Bonus for critical fixes
        score += min(critical_fixed * 10, 40)
        
        score = min(score, 100)
        
        if score >= 80:
            return f"Excellent ({score:.0f}/100)"
        elif score >= 60:
            return f"Good ({score:.0f}/100)"
        elif score >= 40:
            return f"Fair ({score:.0f}/100)"
        else:
            return f"Minimal ({score:.0f}/100)"
