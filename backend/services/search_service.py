"""
Advanced Search and Filtering Service
Smart search across files with custom filters and saved patterns
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import re


class SearchFilter:
    """Represents a search filter configuration"""
    
    def __init__(self, name: str, conditions: Dict):
        self.name = name
        self.conditions = conditions
        self.created_at = datetime.utcnow()


class SearchService:
    """Handles advanced search and filtering operations"""
    
    def __init__(self, db):
        self.db = db
        self.saved_filters = {}
    
    async def search_files(self, project_id: str, query: str, 
                          filters: Optional[Dict] = None) -> List[Dict]:
        """
        Smart search across files with various criteria
        
        Args:
            project_id: Project identifier
            query: Search term (file name, content, pattern)
            filters: Additional filters (severity, complexity, etc.)
        """
        # Get all files for the project
        files = await self.db.get_files_by_project(project_id)
        
        if not files:
            return []
        
        # Apply text search
        results = self._apply_text_search(files, query)
        
        # Apply filters
        if filters:
            results = self._apply_filters(results, filters)
        
        # Sort by relevance
        results = self._sort_by_relevance(results, query)
        
        return results
    
    def _apply_text_search(self, files: List[Dict], query: str) -> List[Dict]:
        """Apply text search across file names and paths"""
        if not query:
            return files
        
        query_lower = query.lower()
        matching_files = []
        
        for file in files:
            score = 0
            
            # Check file name
            file_name = file.get('path', '').lower()
            if query_lower in file_name:
                score += 10
                if file_name.endswith(query_lower):
                    score += 5
            
            # Check file type
            if query_lower in file.get('type', '').lower():
                score += 5
            
            # Check issues/smells
            for issue in file.get('issues', []):
                if query_lower in issue.get('message', '').lower():
                    score += 3
            
            if score > 0:
                file['relevance_score'] = score
                matching_files.append(file)
        
        return matching_files
    
    def _apply_filters(self, files: List[Dict], filters: Dict) -> List[Dict]:
        """Apply custom filters to file list"""
        filtered = files
        
        # Severity filter
        if 'severity' in filters:
            severity_levels = filters['severity']
            if not isinstance(severity_levels, list):
                severity_levels = [severity_levels]
            filtered = [
                f for f in filtered
                if self._get_severity(f) in severity_levels
            ]
        
        # Risk score filter
        if 'min_risk_score' in filters:
            min_score = filters['min_risk_score']
            filtered = [
                f for f in filtered
                if f.get('risk_score', 0) >= min_score
            ]
        
        if 'max_risk_score' in filters:
            max_score = filters['max_risk_score']
            filtered = [
                f for f in filtered
                if f.get('risk_score', 0) <= max_score
            ]
        
        # Complexity filter
        if 'min_complexity' in filters:
            min_complexity = filters['min_complexity']
            filtered = [
                f for f in filtered
                if f.get('complexity', 0) >= min_complexity
            ]
        
        # Duplication filter
        if 'has_duplication' in filters:
            has_dup = filters['has_duplication']
            filtered = [
                f for f in filtered
                if (f.get('duplication_percentage', 0) > 0) == has_dup
            ]
        
        # File type filter
        if 'file_types' in filters:
            types = filters['file_types']
            if not isinstance(types, list):
                types = [types]
            filtered = [
                f for f in filtered
                if f.get('type') in types
            ]
        
        # Date range filter
        if 'date_from' in filters or 'date_to' in filters:
            filtered = self._filter_by_date(filtered, filters)
        
        # Issue count filter
        if 'min_issues' in filters:
            min_issues = filters['min_issues']
            filtered = [
                f for f in filtered
                if len(f.get('issues', [])) >= min_issues
            ]
        
        return filtered
    
    def _get_severity(self, file: Dict) -> str:
        """Determine file severity based on risk score"""
        risk_score = file.get('risk_score', 0)
        if risk_score >= 0.8:
            return 'critical'
        elif risk_score >= 0.6:
            return 'high'
        elif risk_score >= 0.4:
            return 'medium'
        else:
            return 'low'
    
    def _filter_by_date(self, files: List[Dict], filters: Dict) -> List[Dict]:
        """Filter files by date range"""
        date_from = filters.get('date_from')
        date_to = filters.get('date_to')
        
        filtered = []
        for file in files:
            file_date = file.get('scanned_at', file.get('created_at'))
            if not file_date:
                continue
            
            if date_from and file_date < date_from:
                continue
            if date_to and file_date > date_to:
                continue
            
            filtered.append(file)
        
        return filtered
    
    def _sort_by_relevance(self, files: List[Dict], query: str) -> List[Dict]:
        """Sort files by relevance score"""
        return sorted(files, key=lambda f: f.get('relevance_score', 0), reverse=True)
    
    async def save_filter(self, user_id: str, filter_name: str, 
                         conditions: Dict) -> Dict:
        """Save a custom filter for reuse"""
        filter_key = f"{user_id}:{filter_name}"
        
        search_filter = SearchFilter(filter_name, conditions)
        self.saved_filters[filter_key] = {
            "name": filter_name,
            "user_id": user_id,
            "conditions": conditions,
            "created_at": search_filter.created_at.isoformat()
        }
        
        return {
            "status": "filter_saved",
            "filter_name": filter_name,
            "key": filter_key
        }
    
    async def get_saved_filters(self, user_id: str) -> List[Dict]:
        """Get all saved filters for a user"""
        user_filters = [
            f for key, f in self.saved_filters.items()
            if key.startswith(f"{user_id}:")
        ]
        return user_filters
    
    async def delete_filter(self, user_id: str, filter_name: str) -> Dict:
        """Delete a saved filter"""
        filter_key = f"{user_id}:{filter_name}"
        if filter_key in self.saved_filters:
            del self.saved_filters[filter_key]
            return {"status": "filter_deleted"}
        return {"status": "filter_not_found"}
    
    async def apply_saved_filter(self, project_id: str, user_id: str, 
                                filter_name: str, query: str = "") -> List[Dict]:
        """Apply a saved filter to search"""
        filter_key = f"{user_id}:{filter_name}"
        saved_filter = self.saved_filters.get(filter_key)
        
        if not saved_filter:
            raise ValueError("Filter not found")
        
        return await self.search_files(
            project_id, query, saved_filter['conditions']
        )
    
    async def advanced_pattern_search(self, project_id: str, 
                                     pattern: str, regex: bool = False) -> List[Dict]:
        """Search for code patterns using regex"""
        files = await self.db.get_files_by_project(project_id)
        
        if regex:
            try:
                pattern_re = re.compile(pattern, re.IGNORECASE)
            except re.error:
                raise ValueError("Invalid regex pattern")
        
        matching_files = []
        for file in files:
            # Check in code smells
            for smell in file.get('code_smells', []):
                code_snippet = smell.get('code_snippet', '')
                message = smell.get('message', '')
                
                if regex:
                    if pattern_re.search(code_snippet) or pattern_re.search(message):
                        matching_files.append(file)
                        break
                else:
                    if pattern.lower() in code_snippet.lower() or pattern.lower() in message.lower():
                        matching_files.append(file)
                        break
        
        return matching_files
    
    async def multi_file_comparison_search(self, project_id: str, 
                                          file_paths: List[str]) -> Dict:
        """Compare multiple files side by side"""
        files = await self.db.get_files_by_project(project_id)
        
        compared_files = {}
        for path in file_paths:
            matching_file = next((f for f in files if f.get('path') == path), None)
            if matching_file:
                compared_files[path] = {
                    "risk_score": matching_file.get('risk_score', 0),
                    "complexity": matching_file.get('complexity', 0),
                    "issues": len(matching_file.get('issues', [])),
                    "smells": len(matching_file.get('code_smells', [])),
                    "lines_of_code": matching_file.get('lines_of_code', 0),
                    "duplication": matching_file.get('duplication_percentage', 0)
                }
        
        return {
            "files_compared": len(compared_files),
            "comparison": compared_files
        }
