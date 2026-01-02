"""
Dependency Graph Service - Analyzes file imports and generates dependency graph data.
"""

import os
import ast
import re
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict


class DependencyAnalyzer:
    """Analyzes code dependencies and generates graph data for visualization."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.nodes: List[Dict[str, Any]] = []
        self.links: List[Dict[str, Any]] = []
        
    def analyze(self) -> Dict[str, Any]:
        """Analyze all files and return dependency graph data."""
        python_files = list(self.repo_path.rglob("*.py"))
        js_files = list(self.repo_path.rglob("*.js"))
        jsx_files = list(self.repo_path.rglob("*.jsx"))
        ts_files = list(self.repo_path.rglob("*.ts"))
        tsx_files = list(self.repo_path.rglob("*.tsx"))
        
        all_files = python_files + js_files + jsx_files + ts_files + tsx_files
        
        ignore_dirs = {'node_modules', 'venv', '.venv', '__pycache__', '.git', 'dist', 'build'}
        all_files = [f for f in all_files if not any(d in f.parts for d in ignore_dirs)]
        
        file_index = self._build_file_index(all_files)
        
        for file_path in all_files:
            self._analyze_file(file_path, file_index)
        
        self._calculate_node_metrics()
        
        return {
            "nodes": self.nodes,
            "links": self.links,
            "edges": self.links,  # Add both formats for compatibility
            "stats": {
                "total_files": len(self.nodes),
                "total_connections": len(self.links),
                "languages": self._get_language_stats()
            }
        }
    
    def _build_file_index(self, files: List[Path]) -> Dict[str, Path]:
        index = {}
        for f in files:
            name = f.stem
            index[name] = f
            try:
                rel = f.relative_to(self.repo_path)
                index[str(rel)] = f
                module_path = str(rel).replace(os.sep, '.').replace('/', '.')
                if module_path.endswith('.py'):
                    module_path = module_path[:-3]
                index[module_path] = f
            except ValueError:
                pass
        return index
    
    def _analyze_file(self, file_path: Path, file_index: Dict[str, Path]):
        try:
            rel_path = str(file_path.relative_to(self.repo_path))
        except ValueError:
            rel_path = str(file_path)
        
        ext = file_path.suffix.lower()
        if ext == '.py':
            file_type = 'python'
            imports = self._get_python_imports(file_path)
        elif ext in ['.js', '.jsx']:
            file_type = 'javascript'
            imports = self._get_js_imports(file_path)
        elif ext in ['.ts', '.tsx']:
            file_type = 'typescript'
            imports = self._get_js_imports(file_path)
        else:
            return
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            loc = len(content.splitlines())
        except:
            loc = 0
        
        node_id = rel_path.replace('\\', '/')
        self.nodes.append({
            "id": node_id,
            "name": file_path.name,
            "label": file_path.name,  # Add label field
            "path": rel_path,
            "type": file_type,
            "metrics": {"lines": loc, "complexity": 0},
            "risk": 0
        })
        
        for imp in imports:
            resolved = self._resolve_import(imp, file_path, file_index)
            if resolved:
                try:
                    target_rel = str(resolved.relative_to(self.repo_path)).replace('\\', '/')
                except ValueError:
                    target_rel = str(resolved).replace('\\', '/')
                self.links.append({"source": node_id, "target": target_rel, "type": "import"})
    
    def _get_python_imports(self, file_path: Path) -> List[str]:
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
        imports = []
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            imports.extend(re.findall(r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]', content))
            imports.extend(re.findall(r'import\s+[\'"]([^\'"]+)[\'"]', content))
            imports.extend(re.findall(r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)', content))
        except:
            pass
        return imports
    
    def _resolve_import(self, import_name: str, source_file: Path, file_index: Dict[str, Path]) -> Path:
        external = ('react', 'vue', 'angular', 'express', 'lodash', 'axios', 'moment',
                    'numpy', 'pandas', 'django', 'flask', 'fastapi', 'sqlalchemy',
                    'requests', '@', 'framer', 'recharts', 'tailwind', 'vite')
        if import_name.startswith(external):
            return None
        if import_name in file_index:
            return file_index[import_name]
        if import_name.startswith('.'):
            source_dir = source_file.parent
            rel_path = import_name.lstrip('./').replace('/', os.sep)
            for ext in ['.py', '.js', '.jsx', '.ts', '.tsx']:
                candidate = source_dir / (rel_path + ext)
                if candidate.exists():
                    return candidate
        parts = import_name.split('.')
        for part in parts:
            if part in file_index:
                return file_index[part]
        return None
    
    def _calculate_node_metrics(self):
        connections = defaultdict(int)
        for link in self.links:
            connections[link["source"]] += 1
            connections[link["target"]] += 1
        for node in self.nodes:
            conn_count = connections.get(node["id"], 0)
            node["metrics"]["complexity"] = min(100, conn_count * 10)
            node["risk"] = min(100, conn_count * 5)
    
    def _get_language_stats(self) -> Dict[str, int]:
        stats = defaultdict(int)
        for node in self.nodes:
            stats[node["type"]] += 1
        return dict(stats)


_dependency_cache: Dict[str, Dict] = {}


async def get_dependency_graph(project_id: str) -> Dict[str, Any]:
    """Get dependency graph for a project."""
    from services.db import db
    
    if project_id in _dependency_cache:
        return _dependency_cache[project_id]
    
    project = await db.get_project(project_id)
    if not project:
        return {"nodes": [], "links": [], "error": "Project not found"}
    
    repo_path = project.get("local_path")
    if not repo_path or not os.path.exists(repo_path):
        return {"nodes": [], "links": [], "message": "Repository not available locally."}
    
    try:
        analyzer = DependencyAnalyzer(repo_path)
        result = analyzer.analyze()
        _dependency_cache[project_id] = result
        return result
    except Exception as e:
        return {"nodes": [], "links": [], "error": str(e)}
