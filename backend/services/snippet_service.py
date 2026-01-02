"""
Code Snippet Service
Displays actual code snippets showing problematic areas with context
"""

from typing import List, Dict, Optional
import os


class CodeSnippetService:
    """Manages code snippet extraction and display"""
    
    def __init__(self, db):
        self.db = db
    
    async def get_snippet_with_context(self, file_path: str, line_number: int,
                                      context_lines: int = 5) -> Dict:
        """
        Get code snippet with surrounding context
        
        Args:
            file_path: Path to the file
            line_number: Line number of the issue
            context_lines: Number of lines before/after to include
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            start_line = max(0, line_number - context_lines - 1)
            end_line = min(len(lines), line_number + context_lines)
            
            snippet = {
                "file_path": file_path,
                "line_number": line_number,
                "context_lines": context_lines,
                "snippet": ''.join(lines[start_line:end_line]),
                "line_mapping": list(range(start_line + 1, end_line + 1)),
                "issue_line_index": line_number - start_line - 1
            }
            
            return snippet
        except Exception as e:
            return {"error": str(e)}
    
    async def get_file_issues_with_snippets(self, project_id: str, 
                                           file_path: str) -> Dict:
        """Get all issues in a file with code snippets"""
        file_data = await self.db.get_file_by_path(project_id, file_path)
        
        if not file_data:
            return {"error": "File not found"}
        
        issues_with_snippets = []
        
        for issue in file_data.get('issues', []):
            line_num = issue.get('line', 0)
            if line_num > 0:
                snippet = await self.get_snippet_with_context(file_path, line_num)
                issues_with_snippets.append({
                    "issue": issue,
                    "snippet": snippet
                })
        
        return {
            "file_path": file_path,
            "total_issues": len(issues_with_snippets),
            "issues": issues_with_snippets
        }
    
    async def get_before_after_examples(self, project_id: str) -> List[Dict]:
        """
        Get before/after refactoring examples from scan history
        """
        scans = await self.db.get_scan_history(project_id, limit=10)
        
        if len(scans) < 2:
            return []
        
        examples = []
        
        for i in range(len(scans) - 1):
            current_scan = scans[i]
            previous_scan = scans[i + 1]
            
            # Find files that improved
            for curr_file in current_scan.get('files', []):
                prev_file = next(
                    (f for f in previous_scan.get('files', []) 
                     if f['path'] == curr_file['path']),
                    None
                )
                
                if prev_file:
                    # Check if quality improved
                    curr_issues = len(curr_file.get('issues', []))
                    prev_issues = len(prev_file.get('issues', []))
                    
                    if prev_issues > curr_issues:
                        examples.append({
                            "file_path": curr_file['path'],
                            "improvement": {
                                "issues_reduced": prev_issues - curr_issues,
                                "previous_risk": prev_file.get('risk_score', 0),
                                "current_risk": curr_file.get('risk_score', 0)
                            },
                            "scan_dates": {
                                "before": previous_scan.get('timestamp'),
                                "after": current_scan.get('timestamp')
                            }
                        })
        
        return examples
    
    async def get_line_by_line_issues(self, file_path: str) -> Dict:
        """Map issues to specific lines for inline display"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # This would be populated from actual analysis
            line_issues = {}
            
            return {
                "file_path": file_path,
                "total_lines": len(lines),
                "lines_with_issues": line_issues
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def format_snippet_for_display(self, snippet: Dict, 
                                        highlight_line: Optional[int] = None) -> str:
        """Format snippet with syntax highlighting markers"""
        lines = snippet['snippet'].split('\n')
        formatted = []
        
        for i, line in enumerate(lines):
            line_num = snippet['line_mapping'][i] if i < len(snippet['line_mapping']) else i + 1
            prefix = ">>> " if line_num == highlight_line else "    "
            formatted.append(f"{prefix}{line_num:4d} | {line}")
        
        return '\n'.join(formatted)
