"""
Team Analytics and Dashboard Service
Enhanced team productivity metrics, cost savings, and leaderboards
"""

from typing import Dict, List
from datetime import datetime, timedelta


class TeamAnalyticsService:
    """Advanced team analytics and performance tracking"""
    
    def __init__(self, db):
        self.db = db
    
    async def get_team_productivity(self, project_id: str, days: int = 30) -> Dict:
        """Calculate team productivity metrics"""
        scans = await self.db.get_scan_history(project_id, limit=days)
        
        if len(scans) < 2:
            return {"error": "Insufficient data"}
        
        first_scan = scans[-1]
        latest_scan = scans[0]
        
        files_improved = 0
        files_degraded = 0
        total_issues_fixed = 0
        
        for latest_file in latest_scan.get('files', []):
            first_file = next(
                (f for f in first_scan.get('files', []) if f['path'] == latest_file['path']),
                None
            )
            
            if first_file:
                latest_issues = len(latest_file.get('issues', []))
                first_issues = len(first_file.get('issues', []))
                
                if latest_issues < first_issues:
                    files_improved += 1
                    total_issues_fixed += (first_issues - latest_issues)
                elif latest_issues > first_issues:
                    files_degraded += 1
        
        return {
            "time_period_days": days,
            "files_improved": files_improved,
            "files_degraded": files_degraded,
            "total_issues_fixed": total_issues_fixed,
            "net_quality_change": files_improved - files_degraded,
            "improvement_rate": (files_improved / len(latest_scan.get('files', [])) * 100) if latest_scan.get('files') else 0
        }
    
    async def calculate_cost_savings(self, project_id: str, days: int = 30) -> Dict:
        """Calculate cost savings from bug prevention"""
        productivity = await self.get_team_productivity(project_id, days)
        
        # Industry averages
        CRITICAL_BUG_COST = 5000
        HIGH_BUG_COST = 2000
        MEDIUM_BUG_COST = 500
        DEV_HOUR_COST = 75
        
        issues_fixed = productivity.get('total_issues_fixed', 0)
        
        critical_bugs = int(issues_fixed * 0.1)
        high_bugs = int(issues_fixed * 0.3)
        medium_bugs = int(issues_fixed * 0.6)
        
        total_savings = (
            critical_bugs * CRITICAL_BUG_COST +
            high_bugs * HIGH_BUG_COST +
            medium_bugs * MEDIUM_BUG_COST
        )
        
        hours_saved = critical_bugs * 40 + high_bugs * 16 + medium_bugs * 4
        
        return {
            "time_period_days": days,
            "total_cost_savings": total_savings,
            "breakdown": {
                "critical_bugs_prevented": critical_bugs,
                "high_bugs_prevented": high_bugs,
                "medium_bugs_prevented": medium_bugs
            },
            "developer_hours_saved": hours_saved,
            "hourly_cost_savings": hours_saved * DEV_HOUR_COST
        }
    
    async def get_technology_heatmap(self, project_id: str) -> Dict:
        """Analyze which technologies/languages are riskiest"""
        files = await self.db.get_files_by_project(project_id)
        
        tech_stats = {}
        
        for file in files:
            file_type = file.get('type', 'unknown')
            risk_score = file.get('risk_score', 0)
            
            if file_type not in tech_stats:
                tech_stats[file_type] = {
                    "total_files": 0,
                    "total_risk": 0,
                    "high_risk_files": 0
                }
            
            tech_stats[file_type]["total_files"] += 1
            tech_stats[file_type]["total_risk"] += risk_score
            
            if risk_score >= 0.6:
                tech_stats[file_type]["high_risk_files"] += 1
        
        for tech in tech_stats:
            total_files = tech_stats[tech]["total_files"]
            tech_stats[tech]["average_risk"] = tech_stats[tech]["total_risk"] / total_files
            tech_stats[tech]["risk_percentage"] = (tech_stats[tech]["high_risk_files"] / total_files) * 100
        
        sorted_tech = sorted(
            tech_stats.items(),
            key=lambda x: x[1]["average_risk"],
            reverse=True
        )
        
        return {
            "technologies": dict(sorted_tech),
            "riskiest_technology": sorted_tech[0][0] if sorted_tech else "none"
        }
