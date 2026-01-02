"""
Advanced Reporting Service
Custom report builder with scheduling and multiple export formats
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json


class ReportTemplate:
    """Represents a custom report template"""
    
    def __init__(self, name: str, sections: List[str], format: str = "json"):
        self.name = name
        self.sections = sections
        self.format = format
        self.created_at = datetime.utcnow()


class ReportingService:
    """Advanced reporting with custom builders and schedulers"""
    
    def __init__(self, db):
        self.db = db
        self.templates = {}
        self.scheduled_reports = {}
    
    async def create_custom_report(self, project_id: str, sections: List[str],
                                  format: str = "json") -> Dict:
        """
        Build custom report with selected sections
        
        Available sections:
        - executive_summary
        - risk_metrics
        - code_smells
        - dependencies
        - trends
        - team_performance
        - roi_analysis
        """
        report = {
            "project_id": project_id,
            "generated_at": datetime.utcnow().isoformat(),
            "format": format,
            "sections": {}
        }
        
        if "executive_summary" in sections:
            report["sections"]["executive_summary"] = await self._generate_executive_summary(project_id)
        
        if "risk_metrics" in sections:
            report["sections"]["risk_metrics"] = await self._generate_risk_metrics(project_id)
        
        if "code_smells" in sections:
            report["sections"]["code_smells"] = await self._generate_code_smells_report(project_id)
        
        if "dependencies" in sections:
            report["sections"]["dependencies"] = await self._generate_dependencies_report(project_id)
        
        if "trends" in sections:
            report["sections"]["trends"] = await self._generate_trends_report(project_id)
        
        if "team_performance" in sections:
            report["sections"]["team_performance"] = await self._generate_team_performance(project_id)
        
        if "roi_analysis" in sections:
            report["sections"]["roi_analysis"] = await self._generate_roi_analysis(project_id)
        
        return report
    
    async def _generate_executive_summary(self, project_id: str) -> Dict:
        """Generate executive summary for stakeholders"""
        metrics = await self.db.get_metrics(project_id)
        risks = await self.db.get_risks(project_id)
        
        critical_files = [f for f in risks.get('files', []) if f.get('risk_score', 0) >= 0.8]
        
        return {
            "overall_health": "Good" if metrics.get('quality_score', 0) > 75 else "Needs Attention",
            "quality_score": metrics.get('quality_score', 0),
            "total_files": metrics.get('total_files', 0),
            "critical_files": len(critical_files),
            "key_insights": [
                f"{len(critical_files)} files require immediate attention",
                f"Code complexity: {metrics.get('complexity_score', 0):.1f}",
                f"Test coverage: {metrics.get('test_coverage', 0):.1f}%"
            ],
            "recommended_actions": [
                "Review and refactor critical risk files",
                "Increase test coverage for high-risk modules",
                "Address technical debt in core components"
            ]
        }
    
    async def _generate_risk_metrics(self, project_id: str) -> Dict:
        """Generate detailed risk metrics"""
        risks = await self.db.get_risks(project_id)
        return {
            "high_risk_files": len([f for f in risks.get('files', []) if f.get('risk_score', 0) >= 0.6]),
            "risk_distribution": {
                "critical": len([f for f in risks.get('files', []) if f.get('risk_score', 0) >= 0.8]),
                "high": len([f for f in risks.get('files', []) if 0.6 <= f.get('risk_score', 0) < 0.8]),
                "medium": len([f for f in risks.get('files', []) if 0.4 <= f.get('risk_score', 0) < 0.6]),
                "low": len([f for f in risks.get('files', []) if f.get('risk_score', 0) < 0.4])
            }
        }
    
    async def _generate_code_smells_report(self, project_id: str) -> Dict:
        """Generate code smells report"""
        smells = await self.db.get_smells(project_id)
        return {
            "total_smells": len(smells.get('smells', [])),
            "smell_types": self._categorize_smells(smells.get('smells', []))
        }
    
    async def _generate_dependencies_report(self, project_id: str) -> Dict:
        """Generate dependencies report"""
        return {
            "total_dependencies": 0,
            "outdated_dependencies": [],
            "vulnerable_dependencies": []
        }
    
    async def _generate_trends_report(self, project_id: str) -> Dict:
        """Generate trends report"""
        scans = await self.db.get_scan_history(project_id, limit=30)
        
        if len(scans) < 2:
            return {"error": "Insufficient data for trends"}
        
        return {
            "quality_trend": "improving" if scans[0].get('quality_score', 0) > scans[-1].get('quality_score', 0) else "declining",
            "total_scans": len(scans),
            "time_period": f"{len(scans)} scans"
        }
    
    async def _generate_team_performance(self, project_id: str) -> Dict:
        """Generate team performance metrics"""
        return {
            "files_improved": 0,
            "bugs_prevented": 0,
            "top_contributors": []
        }
    
    async def _generate_roi_analysis(self, project_id: str) -> Dict:
        """Generate ROI analysis"""
        from services.comparison_service import ComparisonService
        comparison_service = ComparisonService(self.db)
        
        roi = await comparison_service.calculate_roi(project_id, days=30)
        return roi
    
    def _categorize_smells(self, smells: List[Dict]) -> Dict:
        """Categorize code smells"""
        categories = {}
        for smell in smells:
            smell_type = smell.get('type', 'unknown')
            categories[smell_type] = categories.get(smell_type, 0) + 1
        return categories
    
    async def save_report_template(self, template_name: str, sections: List[str],
                                  format: str = "json") -> Dict:
        """Save a custom report template"""
        template = ReportTemplate(template_name, sections, format)
        self.templates[template_name] = {
            "name": template_name,
            "sections": sections,
            "format": format,
            "created_at": template.created_at.isoformat()
        }
        return {"status": "template_saved", "template_name": template_name}
    
    async def schedule_report(self, project_id: str, template_name: str,
                             frequency: str, recipients: List[str]) -> Dict:
        """
        Schedule automated report generation
        
        frequency: daily, weekly, monthly
        """
        schedule_id = f"schedule_{datetime.utcnow().timestamp()}"
        
        self.scheduled_reports[schedule_id] = {
            "id": schedule_id,
            "project_id": project_id,
            "template_name": template_name,
            "frequency": frequency,
            "recipients": recipients,
            "created_at": datetime.utcnow().isoformat(),
            "next_run": self._calculate_next_run(frequency),
            "enabled": True
        }
        
        return {
            "status": "report_scheduled",
            "schedule_id": schedule_id,
            "next_run": self.scheduled_reports[schedule_id]["next_run"]
        }
    
    def _calculate_next_run(self, frequency: str) -> str:
        """Calculate next run time for scheduled report"""
        now = datetime.utcnow()
        
        if frequency == "daily":
            next_run = now + timedelta(days=1)
        elif frequency == "weekly":
            next_run = now + timedelta(weeks=1)
        elif frequency == "monthly":
            next_run = now + timedelta(days=30)
        else:
            next_run = now + timedelta(days=1)
        
        return next_run.isoformat()
    
    async def export_report(self, report: Dict, format: str) -> Dict:
        """
        Export report in specified format
        
        Supported formats: json, pdf, csv, excel
        """
        if format == "json":
            return {"data": json.dumps(report, indent=2), "mime_type": "application/json"}
        elif format == "pdf":
            # TODO: Implement PDF generation
            return {"data": "PDF export not yet implemented", "mime_type": "application/pdf"}
        elif format == "csv":
            # TODO: Implement CSV export
            return {"data": "CSV export not yet implemented", "mime_type": "text/csv"}
        elif format == "excel":
            # TODO: Implement Excel export
            return {"data": "Excel export not yet implemented", "mime_type": "application/vnd.ms-excel"}
        else:
            raise ValueError(f"Unsupported format: {format}")
