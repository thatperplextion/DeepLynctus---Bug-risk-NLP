from services.db import get_database
from datetime import datetime

class ReportService:
    @staticmethod
    async def generate_pdf(project_id: str, sections: list[str]) -> bytes:
        """
        Generate a PDF report for the given project.
        Uses ReportLab if available, otherwise returns a formatted text file.
        """
        # Get database instance
        db = get_database()
        
        # Gather data using async methods
        project = await db.get_project(project_id) or {}
        metrics_list = await db.get_metrics(project_id)
        risks_list = await db.get_risks(project_id)
        smells_list = await db.get_smells(project_id)
        
        # Calculate summary stats
        total_files = len(metrics_list)
        avg_risk = sum(r.get('risk_score', 0) for r in risks_list) / max(len(risks_list), 1)
        critical_count = sum(1 for r in risks_list if r.get('risk_score', 0) >= 80)
        high_count = sum(1 for r in risks_list if 60 <= r.get('risk_score', 0) < 80)
        total_smells = len(smells_list)
        
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            from io import BytesIO
            
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            
            # Header
            c.setFont("Helvetica-Bold", 24)
            c.drawString(72, height - 72, "CodeSenseX Analysis Report")
            
            c.setFont("Helvetica", 12)
            c.drawString(72, height - 100, f"Project: {project.get('name', project_id)}")
            c.drawString(72, height - 118, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Summary Section
            c.setFont("Helvetica-Bold", 16)
            c.drawString(72, height - 160, "Executive Summary")
            
            c.setFont("Helvetica", 12)
            y = height - 185
            c.drawString(72, y, f"Total Files Analyzed: {total_files}")
            c.drawString(72, y - 18, f"Average Risk Score: {avg_risk:.1f}/100")
            c.drawString(72, y - 36, f"Critical Issues: {critical_count}")
            c.drawString(72, y - 54, f"High Risk Files: {high_count}")
            c.drawString(72, y - 72, f"Total Code Smells: {total_smells}")
            
            # Top Risky Files
            c.setFont("Helvetica-Bold", 16)
            c.drawString(72, y - 110, "Top Risk Files")
            
            c.setFont("Helvetica", 10)
            sorted_risks = sorted(risks_list, key=lambda x: x.get('risk_score', 0), reverse=True)[:10]
            y_pos = y - 135
            for r in sorted_risks:
                c.drawString(72, y_pos, f"• {r.get('path', 'Unknown')} - Score: {r.get('risk_score', 0)}")
                y_pos -= 15
                if y_pos < 72:
                    c.showPage()
                    y_pos = height - 72
            
            c.save()
            return buffer.getvalue()
            
        except ImportError:
            # Fallback to text report
            report = []
            report.append("=" * 60)
            report.append("       CODESENSEX ANALYSIS REPORT")
            report.append("=" * 60)
            report.append("")
            report.append(f"Project: {project.get('name', project_id)}")
            report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append("")
            report.append("-" * 60)
            report.append("EXECUTIVE SUMMARY")
            report.append("-" * 60)
            report.append(f"Total Files Analyzed: {total_files}")
            report.append(f"Average Risk Score: {avg_risk:.1f}/100")
            report.append(f"Critical Issues: {critical_count}")
            report.append(f"High Risk Files: {high_count}")
            report.append(f"Total Code Smells: {total_smells}")
            report.append("")
            report.append("-" * 60)
            report.append("TOP RISK FILES")
            report.append("-" * 60)
            
            sorted_risks = sorted(risks_list, key=lambda x: x.get('risk_score', 0), reverse=True)[:10]
            for r in sorted_risks:
                report.append(f"  • {r.get('path', 'Unknown')} - Score: {r.get('risk_score', 0)}")
            
            report.append("")
            report.append("=" * 60)
            report.append("End of Report")
            report.append("=" * 60)
            
            return "\n".join(report).encode("utf-8")
