"""
Project Comparison Service - Compare metrics, quality, and issues between two projects.
"""

from typing import Dict, List, Any
from datetime import datetime
from services.db import get_database


class ProjectComparisonService:
    """Service for comparing two projects side by side."""
    
    @staticmethod
    async def compare_projects(project_a_id: str, project_b_id: str) -> Dict[str, Any]:
        """
        Compare two projects comprehensively.
        
        Returns detailed comparison including metrics, risks, smells, and trends.
        """
        db = get_database()
        
        # Get project info
        project_a = await db.get_project(project_a_id)
        project_b = await db.get_project(project_b_id)
        
        if not project_a or not project_b:
            return {
                "error": "One or both projects not found",
                "project_a_found": bool(project_a),
                "project_b_found": bool(project_b)
            }
        
        # Get metrics for both projects
        metrics_a = await db.get_metrics(project_a_id)
        metrics_b = await db.get_metrics(project_b_id)
        
        # Get risks for both projects
        risks_a = await db.get_risks(project_a_id)
        risks_b = await db.get_risks(project_b_id)
        
        # Get smells for both projects
        smells_a = await db.get_smells(project_a_id)
        smells_b = await db.get_smells(project_b_id)
        
        # Calculate summary statistics
        summary_a = ProjectComparisonService._calculate_summary(metrics_a, risks_a, smells_a)
        summary_b = ProjectComparisonService._calculate_summary(metrics_b, risks_b, smells_b)
        
        # Calculate differences and winner
        differences = ProjectComparisonService._calculate_differences(summary_a, summary_b)
        
        return {
            "comparison_id": f"{project_a_id}_vs_{project_b_id}",
            "timestamp": datetime.utcnow().isoformat(),
            "project_a": {
                "id": project_a_id,
                "name": project_a.get("name", "Project A"),
                "repo_url": project_a.get("source_ref", ""),
                "summary": summary_a,
                "metrics_count": len(metrics_a),
                "risks_count": len(risks_a),
                "smells_count": len(smells_a)
            },
            "project_b": {
                "id": project_b_id,
                "name": project_b.get("name", "Project B"),
                "repo_url": project_b.get("source_ref", ""),
                "summary": summary_b,
                "metrics_count": len(metrics_b),
                "risks_count": len(risks_b),
                "smells_count": len(smells_b)
            },
            "differences": differences,
            "winner": ProjectComparisonService._determine_winner(summary_a, summary_b),
            "detailed_comparison": {
                "complexity": ProjectComparisonService._compare_complexity(metrics_a, metrics_b),
                "code_quality": ProjectComparisonService._compare_quality(metrics_a, metrics_b),
                "security": ProjectComparisonService._compare_security(smells_a, smells_b),
                "maintainability": ProjectComparisonService._compare_maintainability(metrics_a, metrics_b)
            }
        }
    
    @staticmethod
    def _calculate_summary(metrics: List[Dict], risks: List[Dict], smells: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics for a project."""
        if not metrics:
            return {
                "total_files": 0,
                "total_loc": 0,
                "avg_complexity": 0,
                "avg_risk": 0,
                "quality_score": 0,
                "critical_issues": 0,
                "high_issues": 0,
                "total_issues": 0
            }
        
        total_loc = sum(m.get("loc", 0) for m in metrics)
        total_complexity = sum(m.get("cyclomatic_max", 0) for m in metrics)
        avg_complexity = total_complexity / len(metrics) if metrics else 0
        
        avg_risk = sum(r.get("risk_score", 0) for r in risks) / len(risks) if risks else 0
        quality_score = 100 - avg_risk
        
        # Handle severity as string or int
        critical_issues = sum(1 for s in smells if str(s.get("severity", "")).lower() == "critical")
        high_issues = sum(1 for s in smells if str(s.get("severity", "")).lower() == "high")
        
        return {
            "total_files": len(metrics),
            "total_loc": total_loc,
            "avg_complexity": round(avg_complexity, 2),
            "avg_risk": round(avg_risk, 2),
            "quality_score": round(quality_score, 2),
            "critical_issues": critical_issues,
            "high_issues": high_issues,
            "total_issues": len(smells)
        }
    
    @staticmethod
    def _calculate_differences(summary_a: Dict, summary_b: Dict) -> Dict[str, Any]:
        """Calculate percentage differences between two summaries."""
        differences = {}
        
        for key in ["total_files", "total_loc", "avg_complexity", "avg_risk", 
                    "quality_score", "critical_issues", "high_issues", "total_issues"]:
            val_a = summary_a.get(key, 0)
            val_b = summary_b.get(key, 0)
            
            if val_a == 0 and val_b == 0:
                diff_pct = 0
            elif val_a == 0:
                diff_pct = 100
            else:
                diff_pct = ((val_b - val_a) / val_a) * 100
            
            differences[key] = {
                "absolute": round(val_b - val_a, 2),
                "percentage": round(diff_pct, 2),
                "better": "b" if (
                    # For these metrics, lower is better
                    (key in ["avg_complexity", "avg_risk", "critical_issues", "high_issues", "total_issues"] and val_b < val_a) or
                    # For these metrics, higher is better
                    (key in ["quality_score"] and val_b > val_a)
                ) else ("a" if val_a != val_b else "tie")
            }
        
        return differences
    
    @staticmethod
    def _determine_winner(summary_a: Dict, summary_b: Dict) -> Dict[str, Any]:
        """Determine which project has better overall quality."""
        score_a = 0
        score_b = 0
        
        # Quality score (higher is better)
        if summary_a["quality_score"] > summary_b["quality_score"]:
            score_a += 3
        elif summary_b["quality_score"] > summary_a["quality_score"]:
            score_b += 3
        
        # Complexity (lower is better)
        if summary_a["avg_complexity"] < summary_b["avg_complexity"]:
            score_a += 2
        elif summary_b["avg_complexity"] < summary_a["avg_complexity"]:
            score_b += 2
        
        # Critical issues (lower is better)
        if summary_a["critical_issues"] < summary_b["critical_issues"]:
            score_a += 3
        elif summary_b["critical_issues"] < summary_a["critical_issues"]:
            score_b += 3
        
        # Total issues (lower is better)
        if summary_a["total_issues"] < summary_b["total_issues"]:
            score_a += 1
        elif summary_b["total_issues"] < summary_a["total_issues"]:
            score_b += 1
        
        if score_a > score_b:
            winner = "project_a"
            margin = "significant" if score_a - score_b >= 4 else "slight"
        elif score_b > score_a:
            winner = "project_b"
            margin = "significant" if score_b - score_a >= 4 else "slight"
        else:
            winner = "tie"
            margin = "equal"
        
        return {
            "winner": winner,
            "margin": margin,
            "score_a": score_a,
            "score_b": score_b,
            "summary": f"Project {'A' if winner == 'project_a' else 'B' if winner == 'project_b' else 'A and B are'} {'wins by a ' + margin + ' margin' if winner != 'tie' else 'tied'}"
        }
    
    @staticmethod
    def _compare_complexity(metrics_a: List[Dict], metrics_b: List[Dict]) -> Dict[str, Any]:
        """Compare code complexity between projects."""
        if not metrics_a or not metrics_b:
            return {"available": False}
        
        complexity_a = [m.get("cyclomatic_max", 0) for m in metrics_a]
        complexity_b = [m.get("cyclomatic_max", 0) for m in metrics_b]
        
        return {
            "available": True,
            "project_a": {
                "max": max(complexity_a) if complexity_a else 0,
                "avg": sum(complexity_a) / len(complexity_a) if complexity_a else 0,
                "files_over_10": sum(1 for c in complexity_a if c > 10)
            },
            "project_b": {
                "max": max(complexity_b) if complexity_b else 0,
                "avg": sum(complexity_b) / len(complexity_b) if complexity_b else 0,
                "files_over_10": sum(1 for c in complexity_b if c > 10)
            }
        }
    
    @staticmethod
    def _compare_quality(metrics_a: List[Dict], metrics_b: List[Dict]) -> Dict[str, Any]:
        """Compare code quality metrics."""
        if not metrics_a or not metrics_b:
            return {"available": False}
        
        def calc_quality_metrics(metrics):
            comment_ratios = [m.get("comment_ratio", 0) for m in metrics]
            dup_ratios = [m.get("dup_ratio", 0) for m in metrics]
            
            return {
                "avg_comment_ratio": sum(comment_ratios) / len(comment_ratios) if comment_ratios else 0,
                "avg_duplication": sum(dup_ratios) / len(dup_ratios) if dup_ratios else 0,
                "well_documented": sum(1 for c in comment_ratios if c > 0.2)
            }
        
        return {
            "available": True,
            "project_a": calc_quality_metrics(metrics_a),
            "project_b": calc_quality_metrics(metrics_b)
        }
    
    @staticmethod
    def _compare_security(smells_a: List[Dict], smells_b: List[Dict]) -> Dict[str, Any]:
        """Compare security issues."""
        security_types = {"SQL Injection Risk", "Hardcoded Secret", "Database Credentials",
                         "API Key Exposed", "Command Injection Risk"}
        
        def count_security_issues(smells):
            return sum(1 for s in smells if s.get("type", "") in security_types)
        
        sec_a = count_security_issues(smells_a)
        sec_b = count_security_issues(smells_b)
        
        return {
            "available": True,
            "project_a": {"security_issues": sec_a},
            "project_b": {"security_issues": sec_b},
            "winner": "project_a" if sec_a < sec_b else ("project_b" if sec_b < sec_a else "tie")
        }
    
    @staticmethod
    def _compare_maintainability(metrics_a: List[Dict], metrics_b: List[Dict]) -> Dict[str, Any]:
        """Compare maintainability metrics."""
        if not metrics_a or not metrics_b:
            return {"available": False}
        
        def calc_maintainability(metrics):
            avg_loc = sum(m.get("loc", 0) for m in metrics) / len(metrics) if metrics else 0
            avg_functions = sum(m.get("fn_count", 0) for m in metrics) / len(metrics) if metrics else 0
            
            # Maintainability score (0-100)
            score = 100
            if avg_loc > 500:
                score -= 20
            if avg_functions > 20:
                score -= 15
            
            return {
                "avg_file_size": round(avg_loc, 2),
                "avg_functions_per_file": round(avg_functions, 2),
                "maintainability_score": max(0, score)
            }
        
        return {
            "available": True,
            "project_a": calc_maintainability(metrics_a),
            "project_b": calc_maintainability(metrics_b)
        }
