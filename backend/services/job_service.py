from datetime import datetime
import sys
from typing import Dict, Any
from .db import get_database
from .repo_analyzer import repo_analyzer


class JobService:
    @staticmethod
    async def start_scan(project_id: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start a scan for the given project.
        
        1. Get the project's GitHub URL from the database
        2. Clone the repository
        3. Run static analysis (AST parsing, complexity, etc.)
        4. Detect code smells
        5. Calculate risk scores
        6. Store all results in the database
        
        Returns scan results summary.
        """
        db = get_database()
        
        # Get project info
        project = await db.get_project(project_id)
        if not project:
            return {"error": "Project not found", "started_at": datetime.utcnow().isoformat()}
        
        github_url = project.get("source_ref", "")
        if not github_url:
            return {"error": "No GitHub URL found for project", "started_at": datetime.utcnow().isoformat()}
        
        # Analyze the repository
        print(f"🔍 Starting analysis of {github_url}...", flush=True)
        results = await repo_analyzer.analyze_github_repo(github_url)
        
        if "error" in results and results.get("error"):
            return {"error": results["error"], "started_at": datetime.utcnow().isoformat()}
        
        # Store results in database
        metrics = results.get("metrics", [])
        risks = results.get("risks", [])
        smells = results.get("smells", [])
        
        db = get_database()
        await db.set_metrics(project_id, metrics)
        await db.set_risks(project_id, risks)
        await db.set_smells(project_id, smells)
        
        print(f"✅ Analysis complete: {len(metrics)} files, {len(smells)} smells, {len(risks)} risk scores", flush=True)
        
        return {
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
            "summary": results.get("summary", {}),
            "files_analyzed": len(metrics),
            "smells_found": len(smells),
            "status": "completed"
        }
