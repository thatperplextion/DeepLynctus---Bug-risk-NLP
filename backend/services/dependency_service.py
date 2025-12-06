"""
Dependency Graph Service - Analyzes file imports and generates dependency graph data.
"""

import os
import ast
import re
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict


class DependencyAnalyzer:
    """Analyzes code dependencies and generates graph data for visualization."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.nodes: List[Dict[str, Any]] = []
        self.edges: List[Dict[str, Any]] = []
        self.file_metrics: Dict[str, Dict] = {}
        
    def analyze(self) -> Dict[str, Any]:
        """Analyze all files and return dependency graph data."""
        # Find all source files
        python_files = list(self.repo_path.rglob("*.py"))
        js_files = list(self.repo_path.rglob("*.js"))
        jsx_files = list(self.repo_path.rglob("*.jsx"))
        ts_files = list(self.repo_path.rglob("*.ts"))
        tsx_files = list(self.repo_path.rglob("*.tsx"))
        
        all_files = python_files + js_files + jsx_files + ts_files + tsx_files
        
        # Filter out common directories to ignore
        ignore_dirs = {'node_modules', 'venv', '.venv', '__pycache__', '.git', 'dist', 'build'}
        all_files = [f for f in all_files if not any(d in f.parts for d in ignore_dirs)]
        
        # Build file index for resolution
        file_index = self._build_file_index(all_files)
        
        # Analyze each file
        for file_path in all_files:
            self._analyze_file(file_path, file_index)
        
        # Calculate node sizes based on connections
        self._calculate_node_metrics()
        
        return {
            "nodes": self.nodes,
            "edges": self.edges,
            "stats": {
                "total_files": len(self.nodes),
                "total_connections": len(self.edges),
                "languages": self._get_language_stats(),
                "most_connected": self._get_most_connected(5),
                "circular_dependencies": self._find_circular_deps()
            }
        }
    
    def _build_file_index(self, files: List[Path]) -> Dict[str, Path]:
        """Build index for resolving imports."""
        index = {}
        for f in files:
            # Index by filename without extension
            name = f.stem
            index[name] = f
            
            # Index by relative path
            try:
                rel = f.relative_to(self.repo_path)
                index[str(rel)] = f
                # Also index module-style paths
                module_path = str(rel).replace(os.sep, '.').replace('/', '.')
                if module_path.endswith('.py'):
                    module_path = module_path[:-3]
                index[module_path] = f
            except ValueError:
                pass
        return index
    
    def _analyze_file(self, file_path: Path, file_index: Dict[str, Path]):
        """Analyze a single file for imports and metrics."""
        try:
            rel_path = str(file_path.relative_to(self.repo_path))
        except ValueError:
            rel_path = str(file_path)
        
        # Determine language
        ext = file_path.suffix.lower()
        if ext == '.py':
            language = 'python'
            imports = self._get_python_imports(file_path)
        elif ext in ['.js', '.jsx', '.ts', '.tsx']:
            language = 'javascript'
            imports = self._get_js_imports(file_path)
        else:
            return
        
        # Get file size for node sizing
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            loc = len(content.splitlines())
        except:
            loc = 0
        
        # Determine folder/group
        parts = rel_path.split(os.sep)
        group = parts[0] if len(parts) > 1 else 'root'
        
        # Add node
        node_id = rel_path
        self.nodes.append({
            "id": node_id,
            "label": file_path.name,
            "path": rel_path,
            "language": language,
            "group": group,
            "loc": loc,
            "size": max(10, min(50, loc / 10)),  # Size based on LOC
            "imports_count": 0,
            "imported_by_count": 0
        })
        
        # Resolve imports and add edges
        for imp in imports:
            resolved = self._resolve_import(imp, file_path, file_index)
            if resolved:
                try:
                    target_rel = str(resolved.relative_to(self.repo_path))
                except ValueError:
                    target_rel = str(resolved)
                
                self.edges.append({
                    "source": node_id,
                    "target": target_rel,
                    "type": "import"
                })
    
    def _get_python_imports(self, file_path: Path) -> List[str]:
        """Extract imports from Python file."""
        imports = []
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except:
            pass
        return imports
    
    def _get_js_imports(self, file_path: Path) -> List[str]:
        """Extract imports from JavaScript/TypeScript file."""
        imports = []
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # ES6 imports: import x from 'module'
            es6_pattern = r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]'
            imports.extend(re.findall(es6_pattern, content))
            
            # ES6 imports: import 'module'
            direct_pattern = r'import\s+[\'"]([^\'"]+)[\'"]'
            imports.extend(re.findall(direct_pattern, content))
            
            # require() calls
            require_pattern = r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
            imports.extend(re.findall(require_pattern, content))
            
        except:
            pass
        return imports
    
    def _resolve_import(self, import_name: str, source_file: Path, file_index: Dict[str, Path]) -> Path:
        """Try to resolve an import to a file in the project."""
        # Skip external packages
        if import_name.startswith(('react', 'vue', 'angular', 'express', 'lodash', 
                                   'axios', 'moment', 'numpy', 'pandas', 'django',
                                   'flask', 'fastapi', 'sqlalchemy', 'requests',
                                   '@', 'framer', 'recharts', 'tailwind')):
            return None
        
        # Try direct match
        if import_name in file_index:
            return file_index[import_name]
        
        # Try relative resolution
        if import_name.startswith('.'):
            # Relative import
            source_dir = source_file.parent
            rel_path = import_name.lstrip('.')
            levels_up = len(import_name) - len(import_name.lstrip('.'))
            
            for _ in range(levels_up - 1):
                source_dir = source_dir.parent
            
            # Try different extensions
            for ext in ['.py', '.js', '.jsx', '.ts', '.tsx', '/index.js', '/index.ts']:
                candidate = source_dir / (rel_path.replace('.', '/') + ext)
                if candidate.exists():
                    return candidate
        
        # Try matching by name parts
        parts = import_name.split('.')
        for part in parts:
            if part in file_index:
                return file_index[part]
        
        return None
    
    def _calculate_node_metrics(self):
        """Calculate import/imported_by counts for nodes."""
        import_counts = defaultdict(int)
        imported_by_counts = defaultdict(int)
        
        for edge in self.edges:
            import_counts[edge["source"]] += 1
            imported_by_counts[edge["target"]] += 1
        
        for node in self.nodes:
            node["imports_count"] = import_counts[node["id"]]
            node["imported_by_count"] = imported_by_counts[node["id"]]
            # Adjust size based on connections
            connections = node["imports_count"] + node["imported_by_count"]
            node["size"] = max(15, min(60, node["size"] + connections * 2))
    
    def _get_language_stats(self) -> Dict[str, int]:
        """Get count of files by language."""
        stats = defaultdict(int)
        for node in self.nodes:
            stats[node["language"]] += 1
        return dict(stats)
    
    def _get_most_connected(self, n: int) -> List[Dict]:
        """Get the n most connected files."""
        scored = []
        for node in self.nodes:
            score = node["imports_count"] + node["imported_by_count"] * 2  # Weight imported_by higher
            scored.append({"path": node["path"], "connections": score})
        scored.sort(key=lambda x: x["connections"], reverse=True)
        return scored[:n]
    
    def _find_circular_deps(self) -> List[List[str]]:
        """Find circular dependencies."""
        # Build adjacency list
        graph = defaultdict(set)
        for edge in self.edges:
            graph[edge["source"]].add(edge["target"])
        
        # Find cycles using DFS
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph[node]:
                if neighbor not in visited:
                    cycle = dfs(neighbor, path.copy())
                    if cycle:
                        cycles.append(cycle)
                elif neighbor in rec_stack:
                    # Found a cycle
                    idx = path.index(neighbor) if neighbor in path else -1
                    if idx != -1:
                        return path[idx:] + [neighbor]
            
            rec_stack.remove(node)
            return None
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        # Return first 5 cycles
        return cycles[:5]


async def get_dependency_graph(project_id: str, repo_path: str = None) -> Dict[str, Any]:
    """Get dependency graph for a project."""
    from services.db import db
    
    # Try to get cached result first
    cached = await db.dependency_graphs.find_one({"project_id": project_id})
    if cached and not repo_path:
        del cached["_id"]
        return cached
    
    if not repo_path:
        # Try to find repo path from project
        project = await db.projects.find_one({"_id": project_id})
        if project and project.get("local_path"):
            repo_path = project["local_path"]
        else:
            return {"error": "Repository path not found"}
    
    if not os.path.exists(repo_path):
        return {"error": "Repository path does not exist"}
    
    # Analyze dependencies
    analyzer = DependencyAnalyzer(repo_path)
    result = analyzer.analyze()
    
    # Cache result
    cache_doc = {
        "project_id": project_id,
        **result
    }
    await db.dependency_graphs.update_one(
        {"project_id": project_id},
        {"$set": cache_doc},
        upsert=True
    )
    
    return result
