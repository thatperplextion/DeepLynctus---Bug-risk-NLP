"""
Repository Analyzer - Clones and analyzes GitHub repositories for code quality metrics.
Enterprise-grade detection for real-world issues that cause production incidents.
"""

import os
import ast
import tempfile
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import re
from collections import Counter


# ============================================================================
# ENTERPRISE SECURITY PATTERNS - Real vulnerabilities found in production
# ============================================================================
SECURITY_PATTERNS = {
    'sql_injection': [
        r'execute\s*\(\s*["\'].*%s',  # String formatting in SQL
        r'execute\s*\(\s*f["\']',      # f-string in SQL
        r'cursor\.execute\s*\([^,]+\+',  # String concatenation in SQL
        r'\.raw\s*\(\s*["\'].*\{',     # Django raw SQL with format
    ],
    'hardcoded_secrets': [
        r'(?:password|passwd|pwd|secret|api_key|apikey|token|auth)\s*=\s*["\'][^"\']{8,}["\']',
        r'(?:AWS|aws)_(?:SECRET|ACCESS).*=\s*["\'][A-Za-z0-9/+=]{20,}["\']',
        r'-----BEGIN (?:RSA |DSA |EC )?PRIVATE KEY-----',
    ],
    'database_credentials': [
        r'(?:mongodb\+srv|mysql|postgresql|postgres)://[^:]+:[^@]+@',  # DB connection strings with credentials
        r'DATABASE_URL\s*=\s*["\'](?:mysql|postgres|mongodb)://[^"\']+["\']',
    ],
    'api_keys': [
        r'(?:api[_-]?key|apikey|api[_-]?secret)\s*[:=]\s*["\'](?!(?:your|test|demo|example|xxx|000))[A-Za-z0-9_\-]{20,}["\']',
        r'(?:OPENAI|openai|gpt)[_-]?(?:API|api)[_-]?(?:KEY|key)\s*[:=]\s*["\']sk-[A-Za-z0-9]{20,}["\']',
        r'(?:GITHUB|github)[_-]?(?:TOKEN|token|PAT)\s*[:=]\s*["\']gh[ps]_[A-Za-z0-9]{20,}["\']',
    ],
    'aws_credentials': [
        r'AKIA[0-9A-Z]{16}',  # AWS Access Key ID
        r'(?:AWS|aws)[_-]?(?:SECRET|secret)[_-]?(?:ACCESS|access)?[_-]?(?:KEY|key)\s*[:=]\s*["\'][A-Za-z0-9/+=]{40}["\']',
    ],
    'private_keys': [
        r'-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----',
    ],
    'jwt_tokens': [
        r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}',  # JWT format
    ],
    'command_injection': [
        r'os\.system\s*\([^)]*\+',
        r'subprocess\.(?:call|run|Popen)\s*\([^)]*shell\s*=\s*True',
        r'eval\s*\(',
        r'exec\s*\(',
    ],
}

# Compile patterns once for performance
_COMPILED_PATTERNS = {}
for category, patterns in SECURITY_PATTERNS.items():
    _COMPILED_PATTERNS[category] = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in patterns]

# Common performance anti-patterns
PERFORMANCE_PATTERNS = {
    'n_plus_one': r'for\s+\w+\s+in\s+\w+.*:\s*\n\s*.*\.(?:get|filter|find|query)',
    'no_pagination': r'\.(?:all|find)\s*\(\s*\)(?!.*(?:limit|page|skip|offset))',
    'sync_in_async': r'async\s+def\s+\w+.*\n(?:.*\n)*?.*(?:time\.sleep|requests\.)',
}

# Memory leak patterns
MEMORY_PATTERNS = {
    'event_listener_leak': r'addEventListener\s*\([^)]+\)(?!.*removeEventListener)',
    'closure_in_loop': r'for\s*\([^)]+\)\s*\{[^}]*(?:setTimeout|setInterval|addEventListener)',
    'unbounded_cache': r'(?:cache|memo|store)\s*\[[^\]]+\]\s*=(?!.*(?:maxSize|limit|expire))',
}


@dataclass
class FileMetrics:
    path: str
    loc: int
    sloc: int  # Source lines of code (non-blank, non-comment)
    cyclomatic_max: int
    cyclomatic_avg: float
    fn_count: int
    class_count: int
    nesting_max: int
    dup_ratio: float
    comment_ratio: float
    language: str


@dataclass 
class CodeSmell:
    path: str
    type: str
    severity: int  # 1-5
    line: int
    message: str
    suggestion: str


@dataclass
class RiskScore:
    path: str
    risk_score: int  # 0-100
    tier: str  # Critical, High, Medium, Low
    top_features: List[str]


class CyclomaticComplexityVisitor(ast.NodeVisitor):
    """Calculate cyclomatic complexity for Python functions."""
    
    def __init__(self):
        self.complexity = 1  # Base complexity
        
    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)
        
    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)
        
    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)
        
    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.generic_visit(node)
        
    def visit_With(self, node):
        self.complexity += 1
        self.generic_visit(node)
        
    def visit_Assert(self, node):
        self.complexity += 1
        self.generic_visit(node)
        
    def visit_comprehension(self, node):
        self.complexity += 1
        self.generic_visit(node)
        
    def visit_BoolOp(self, node):
        # Each 'and' or 'or' adds to complexity
        self.complexity += len(node.values) - 1
        self.generic_visit(node)
        
    def visit_IfExp(self, node):  # Ternary operator
        self.complexity += 1
        self.generic_visit(node)


class NestingVisitor(ast.NodeVisitor):
    """Calculate maximum nesting depth."""
    
    def __init__(self):
        self.max_depth = 0
        self.current_depth = 0
        
    def _enter_block(self):
        self.current_depth += 1
        self.max_depth = max(self.max_depth, self.current_depth)
        
    def _exit_block(self):
        self.current_depth -= 1
        
    def visit_If(self, node):
        self._enter_block()
        self.generic_visit(node)
        self._exit_block()
        
    def visit_For(self, node):
        self._enter_block()
        self.generic_visit(node)
        self._exit_block()
        
    def visit_While(self, node):
        self._enter_block()
        self.generic_visit(node)
        self._exit_block()
        
    def visit_With(self, node):
        self._enter_block()
        self.generic_visit(node)
        self._exit_block()
        
    def visit_Try(self, node):
        self._enter_block()
        self.generic_visit(node)
        self._exit_block()
        
    def visit_FunctionDef(self, node):
        self._enter_block()
        self.generic_visit(node)
        self._exit_block()
        
    def visit_AsyncFunctionDef(self, node):
        self._enter_block()
        self.generic_visit(node)
        self._exit_block()


class PythonAnalyzer:
    """Analyze Python files for metrics and code smells."""
    
    @staticmethod
    def analyze_file(file_path: Path, relative_path: str) -> tuple[Optional[FileMetrics], List[CodeSmell]]:
        """Analyze a single Python file."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            
            # Basic line counts
            loc = len(lines)
            sloc = sum(1 for line in lines if line.strip() and not line.strip().startswith('#'))
            comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
            comment_ratio = comment_lines / max(loc, 1)
            
            # Parse AST
            try:
                tree = ast.parse(content)
            except SyntaxError:
                # Can't parse, return basic metrics
                return FileMetrics(
                    path=relative_path,
                    loc=loc,
                    sloc=sloc,
                    cyclomatic_max=1,
                    cyclomatic_avg=1.0,
                    fn_count=0,
                    class_count=0,
                    nesting_max=0,
                    dup_ratio=0.0,
                    comment_ratio=comment_ratio,
                    language="python"
                ), []
            
            # Count functions and classes
            functions = [node for node in ast.walk(tree) 
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            
            # Calculate complexity for each function
            complexities = []
            for func in functions:
                visitor = CyclomaticComplexityVisitor()
                visitor.visit(func)
                complexities.append(visitor.complexity)
            
            cyclomatic_max = max(complexities) if complexities else 1
            cyclomatic_avg = sum(complexities) / len(complexities) if complexities else 1.0
            
            # Calculate nesting depth
            nesting_visitor = NestingVisitor()
            nesting_visitor.visit(tree)
            nesting_max = nesting_visitor.max_depth
            
            # Detect code smells
            smells = PythonAnalyzer._detect_smells(tree, lines, relative_path, functions, classes)
            
            metrics = FileMetrics(
                path=relative_path,
                loc=loc,
                sloc=sloc,
                cyclomatic_max=cyclomatic_max,
                cyclomatic_avg=round(cyclomatic_avg, 2),
                fn_count=len(functions),
                class_count=len(classes),
                nesting_max=nesting_max,
                dup_ratio=0.0,  # Would need more sophisticated analysis
                comment_ratio=round(comment_ratio, 3),
                language="python"
            )
            
            return metrics, smells
            
        except Exception as e:
            print(f"Error analyzing {relative_path}: {e}")
            return None, []
    
    @staticmethod
    def _detect_smells(tree: ast.AST, lines: List[str], path: str, 
                       functions: List[ast.AST], classes: List[ast.AST]) -> List[CodeSmell]:
        """
        Enterprise-grade code smell detection for Python.
        Focuses on issues that cause real production incidents.
        """
        smells = []
        content = '\n'.join(lines)
        loc = len(lines)
        
        # Skip security checks for very large files (performance optimization)
        skip_security = loc > 5000
        
        # ============================================================
        # CRITICAL: SECURITY VULNERABILITIES (Severity 5)
        # ============================================================
        
        if not skip_security:
            # SQL Injection Detection
            for pattern in _COMPILED_PATTERNS['sql_injection']:
                match = pattern.search(content)
                if match:
                    line_num = content[:match.start()].count('\n') + 1
                    smells.append(CodeSmell(
                        path=path,
                        type="SQL Injection Risk",
                        severity=5,
                        line=line_num,
                        message="Potential SQL injection: user input may be directly interpolated into SQL query",
                        suggestion="Use parameterized queries: cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))"
                    ))
                    break  # One per file
            
            # Hardcoded Secrets Detection
            for pattern in _COMPILED_PATTERNS['hardcoded_secrets']:
                match = pattern.search(content)
                if match:
                    line_num = content[:match.start()].count('\n') + 1
                    line_content = lines[line_num - 1] if line_num <= len(lines) else ''
                    key_match = re.search(r'(password|secret|key|token|api)', line_content, re.IGNORECASE)
                    key_name = key_match.group(1) if key_match else 'credential'
                    smells.append(CodeSmell(
                        path=path,
                        type="Hardcoded Secret",
                        severity=5,
                        line=line_num,
                        message=f"Hardcoded {key_name} detected - this will be exposed in version control",
                        suggestion="Use environment variables: os.environ.get('SECRET_KEY') or a secrets manager"
                    ))
                    break
            
            # Database Credentials Detection
            for pattern in _COMPILED_PATTERNS['database_credentials']:
                match = pattern.search(content)
                if match:
                    line_num = content[:match.start()].count('\n') + 1
                    smells.append(CodeSmell(
                        path=path,
                        type="Database Credentials Exposed",
                        severity=5,
                        line=line_num,
                        message="Database connection string with embedded credentials - security risk if committed to version control",
                        suggestion="Use environment variables for DB credentials: DB_HOST, DB_USER, DB_PASSWORD. Store connection strings in .env files (gitignored)"
                    ))
                    break
            
            # API Keys Detection
            for pattern in _COMPILED_PATTERNS['api_keys']:
                match = pattern.search(content)
                if match:
                    line_num = content[:match.start()].count('\n') + 1
                    line_content = lines[line_num - 1] if line_num <= len(lines) else ''
                    api_type = "API key"
                    if 'openai' in line_content.lower() or 'gpt' in line_content.lower():
                        api_type = "OpenAI API key"
                    elif 'github' in line_content.lower():
                        api_type = "GitHub token"
                    
                    smells.append(CodeSmell(
                        path=path,
                        type="API Key Exposed",
                        severity=5,
                        line=line_num,
                        message=f"{api_type} hardcoded in source code - immediate security risk",
                        suggestion=f"Rotate the exposed {api_type} immediately. Use environment variables: os.getenv('API_KEY') and add to .gitignore"
                    ))
                    break
            
            # AWS Credentials Detection
            for pattern in _COMPILED_PATTERNS['aws_credentials']:
                match = pattern.search(content)
                if match:
                    line_num = content[:match.start()].count('\n') + 1
                    smells.append(CodeSmell(
                        path=path,
                        type="AWS Credentials Exposed",
                        severity=5,
                        line=line_num,
                        message="AWS credentials detected in code - this grants access to your AWS resources",
                        suggestion="URGENT: Rotate AWS credentials in AWS Console. Use AWS IAM roles, AWS Secrets Manager, or environment variables"
                    ))
                    break
            
            # Private Keys Detection
            for pattern in _COMPILED_PATTERNS['private_keys']:
                match = pattern.search(content)
                if match:
                    line_num = content[:match.start()].count('\n') + 1
                    smells.append(CodeSmell(
                        path=path,
                        type="Private Key Exposed",
                        severity=5,
                        line=line_num,
                        message="Private key found in code - severe security breach if committed",
                        suggestion="Remove private keys from code immediately. Store in secure key management system. Generate new keys if already committed."
                    ))
                    break
            
            # JWT Token Detection  
            for pattern in _COMPILED_PATTERNS['jwt_tokens']:
                match = pattern.search(content)
                if match:
                    line_num = content[:match.start()].count('\n') + 1
                    line_content = lines[line_num - 1] if line_num <= len(lines) else ''
                    if '=' in line_content and 'eyJ' in line_content:
                        smells.append(CodeSmell(
                            path=path,
                            type="JWT Token Hardcoded",
                            severity=5,
                            line=line_num,
                            message="JWT token hardcoded in source - tokens should be generated dynamically or stored securely",
                            suggestion="Never hardcode JWTs. Generate tokens on authentication and store in secure HTTP-only cookies or secure storage"
                        ))
                        break
        
        # Command Injection / Code Execution
        for pattern in _COMPILED_PATTERNS['command_injection']:
            match = pattern.search(content)
            if match:
                line_num = content[:match.start()].count('\n') + 1
                matched_text = match.group(0)[:20]
                smells.append(CodeSmell(
                    path=path,
                    type="Code Injection Risk",
                    severity=5,
                    line=line_num,
                    message=f"Dangerous function '{matched_text}...' can execute arbitrary code",
                    suggestion="Avoid eval/exec. For subprocess, use shell=False and pass args as list"
                ))
                break
        
        # ============================================================
        # HIGH: PERFORMANCE & RELIABILITY ISSUES (Severity 4)
        # ============================================================
        
        # N+1 Query Problem (common in ORMs)
        n_plus_one_pattern = r'for\s+(\w+)\s+in\s+(\w+).*:\s*\n\s*.*\.\s*(?:objects|query|filter|get|find)'
        for match in re.finditer(n_plus_one_pattern, content, re.MULTILINE):
            line_num = content[:match.start()].count('\n') + 1
            smells.append(CodeSmell(
                path=path,
                type="N+1 Query Problem",
                severity=4,
                line=line_num,
                message="Database query inside loop causes N+1 performance issue - each iteration hits the database",
                suggestion="Use select_related/prefetch_related (Django), joinedload (SQLAlchemy), or batch queries"
            ))
        
        # Synchronous I/O in Async Context
        async_sync_pattern = r'async\s+def\s+\w+[^:]+:\s*\n(?:.*\n)*?.*(?:requests\.|urllib\.|time\.sleep|open\()'
        for match in re.finditer(async_sync_pattern, content, re.MULTILINE):
            line_num = content[:match.start()].count('\n') + 1
            smells.append(CodeSmell(
                path=path,
                type="Blocking Call in Async",
                severity=4,
                line=line_num,
                message="Synchronous blocking call inside async function defeats concurrency benefits",
                suggestion="Use aiohttp instead of requests, aiofiles instead of open(), asyncio.sleep instead of time.sleep"
            ))
        
        # Resource Not Closed (file handles, connections)
        resource_leak_pattern = r'(\w+)\s*=\s*open\s*\([^)]+\)(?!.*\bwith\b)(?!.*\.close\(\))'
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'open':
                    # Check if it's in a with statement
                    # This is a simplified check
                    pass
        
        # Check for missing context managers
        for i, line in enumerate(lines):
            if 'open(' in line and 'with ' not in line and '.close()' not in content[content.find(line):content.find(line)+500]:
                smells.append(CodeSmell(
                    path=path,
                    type="Resource Leak Risk",
                    severity=4,
                    line=i + 1,
                    message="File opened without 'with' statement - may not be properly closed on exception",
                    suggestion="Use context manager: with open(filename) as f:"
                ))
                break
        
        # ============================================================
        # HIGH: ERROR HANDLING ANTI-PATTERNS (Severity 4)
        # ============================================================
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                # Bare except (catches KeyboardInterrupt, SystemExit)
                if node.type is None:
                    smells.append(CodeSmell(
                        path=path,
                        type="Bare Except Clause",
                        severity=4,
                        line=node.lineno,
                        message="Bare 'except:' catches KeyboardInterrupt and SystemExit, preventing graceful shutdown",
                        suggestion="Use 'except Exception:' to catch only errors, not system signals"
                    ))
                
                # Swallowed exception (pass or just logging without re-raise in critical code)
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    smells.append(CodeSmell(
                        path=path,
                        type="Swallowed Exception",
                        severity=4,
                        line=node.lineno,
                        message="Exception silently ignored - bugs will be invisible and hard to debug",
                        suggestion="At minimum, log the exception. Consider re-raising or handling appropriately"
                    ))
        
        # ============================================================
        # MEDIUM-HIGH: MAINTAINABILITY ISSUES (Severity 3-4)
        # ============================================================
        
        for func in functions:
            func_name = func.name
            func_lines = func.end_lineno - func.lineno + 1 if hasattr(func, 'end_lineno') else 50
            
            # High Cyclomatic Complexity (bug probability increases exponentially)
            visitor = CyclomaticComplexityVisitor()
            visitor.visit(func)
            if visitor.complexity > 10:
                severity = 5 if visitor.complexity > 25 else 4 if visitor.complexity > 15 else 3
                smells.append(CodeSmell(
                    path=path,
                    type="High Cyclomatic Complexity",
                    severity=severity,
                    line=func.lineno,
                    message=f"Function '{func_name}' has complexity {visitor.complexity} - research shows bug probability increases exponentially above 10",
                    suggestion="Extract conditional logic into well-named helper functions or use strategy/state pattern"
                ))
            
            # Long Function - only flag EXTREMELY long functions (200+ lines is unusual)
            # Skip test files, config files, and generated code
            is_test_file = any(x in path.lower() for x in ['test', 'spec', 'mock', '__pycache__'])
            is_config_file = any(x in path.lower() for x in ['config', 'setting', 'migration'])
            
            if func_lines > 200 and not is_test_file and not is_config_file:
                severity = 2  # Low severity - just informational
                smells.append(CodeSmell(
                    path=path,
                    type="Long Function",
                    severity=severity,
                    line=func.lineno,
                    message=f"Function '{func_name}' is {func_lines} lines - consider if it can be broken down",
                    suggestion="Optional: Extract cohesive blocks if it improves readability"
                ))
            
            # Too Many Parameters (indicates missing abstraction)
            num_args = len(func.args.args) + len(func.args.posonlyargs) + len(func.args.kwonlyargs)
            if num_args > 5:
                severity = 4 if num_args > 7 else 3
                smells.append(CodeSmell(
                    path=path,
                    type="Too Many Parameters",
                    severity=severity,
                    line=func.lineno,
                    message=f"Function '{func_name}' has {num_args} parameters - hard to call correctly and test",
                    suggestion="Group related params into a dataclass/NamedTuple, or split into multiple functions"
                ))
        
        # God Class Detection
        for cls in classes:
            methods = [node for node in ast.walk(cls) 
                      if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
            
            if len(methods) > 15:
                severity = 4 if len(methods) > 25 else 3
                smells.append(CodeSmell(
                    path=path,
                    type="God Class",
                    severity=severity,
                    line=cls.lineno,
                    message=f"Class '{cls.name}' has {len(methods)} methods - violates Single Responsibility Principle",
                    suggestion="Identify different responsibilities and extract into focused collaborating classes"
                ))
        
        # Deep Nesting (cognitive complexity)
        nesting_visitor = NestingVisitor()
        nesting_visitor.visit(tree)
        if nesting_visitor.max_depth > 4:
            severity = 4 if nesting_visitor.max_depth > 5 else 3
            smells.append(CodeSmell(
                path=path,
                type="Deep Nesting",
                severity=severity,
                line=1,
                message=f"Nesting depth {nesting_visitor.max_depth} exceeds cognitive limit - hard to understand control flow",
                suggestion="Use guard clauses (early returns), extract nested blocks to functions, or flatten with helper methods"
            ))
        
        # ============================================================
        # MEDIUM: CODE QUALITY ISSUES (Severity 2-3)
        # ============================================================
        
        # Mutable Default Arguments (common Python gotcha)
        for func in functions:
            for default in func.args.defaults + func.args.kw_defaults:
                if default and isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    smells.append(CodeSmell(
                        path=path,
                        type="Mutable Default Argument",
                        severity=3,
                        line=func.lineno,
                        message=f"Mutable default in '{func.name}' - shared across calls causing subtle bugs",
                        suggestion="Use None as default and create new object: def foo(items=None): items = items or []"
                    ))
                    break
        
        # Global Variable Mutation
        global_pattern = r'^\s*global\s+\w+'
        global_matches = list(re.finditer(global_pattern, content, re.MULTILINE))
        if len(global_matches) > 2:
            smells.append(CodeSmell(
                path=path,
                type="Excessive Global State",
                severity=3,
                line=global_matches[0].start(),
                message=f"Found {len(global_matches)} global variable mutations - makes testing and reasoning difficult",
                suggestion="Pass dependencies explicitly, use dependency injection, or encapsulate in a class"
            ))
        
        return smells


class JavaScriptAnalyzer:
    """Basic analyzer for JavaScript/TypeScript files."""
    
    @staticmethod
    def analyze_file(file_path: Path, relative_path: str) -> tuple[Optional[FileMetrics], List[CodeSmell]]:
        """Analyze a JavaScript/TypeScript file."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            
            loc = len(lines)
            sloc = sum(1 for line in lines if line.strip() and not line.strip().startswith('//'))
            comment_lines = sum(1 for line in lines if line.strip().startswith('//'))
            comment_ratio = comment_lines / max(loc, 1)
            
            # Count functions (basic regex-based)
            fn_patterns = [
                r'function\s+\w+',
                r'const\s+\w+\s*=\s*(?:async\s*)?\(',
                r'(?:async\s+)?(\w+)\s*\([^)]*\)\s*{',
                r'=>',
            ]
            fn_count = sum(len(re.findall(p, content)) for p in fn_patterns[:3])
            
            # Count classes
            class_count = len(re.findall(r'class\s+\w+', content))
            
            # Estimate complexity (count decision points)
            decision_keywords = ['if', 'else', 'for', 'while', 'switch', 'case', 'catch', '&&', '||', '?']
            complexity = 1 + sum(content.count(kw) for kw in decision_keywords)
            
            # Estimate nesting (count bracket depth)
            max_depth = 0
            current_depth = 0
            for char in content:
                if char == '{':
                    current_depth += 1
                    max_depth = max(max_depth, current_depth)
                elif char == '}':
                    current_depth = max(0, current_depth - 1)
            
            smells = JavaScriptAnalyzer._detect_smells(content, lines, relative_path)
            
            metrics = FileMetrics(
                path=relative_path,
                loc=loc,
                sloc=sloc,
                cyclomatic_max=min(complexity, 50),
                cyclomatic_avg=min(complexity / max(fn_count, 1), 20),
                fn_count=fn_count,
                class_count=class_count,
                nesting_max=max_depth,
                dup_ratio=0.0,
                comment_ratio=round(comment_ratio, 3),
                language="javascript" if relative_path.endswith('.js') else "typescript"
            )
            
            return metrics, smells
            
        except Exception as e:
            print(f"Error analyzing {relative_path}: {e}")
            return None, []
    
    @staticmethod
    def _detect_smells(content: str, lines: List[str], path: str) -> List[CodeSmell]:
        """Detect enterprise-grade code smells in JavaScript/TypeScript."""
        smells = []
        loc = len(lines)
        
        # ===== CRITICAL SECURITY VULNERABILITIES (Severity 5) =====
        
        # XSS via innerHTML/dangerouslySetInnerHTML
        xss_patterns = [
            (r'\.innerHTML\s*=', "Direct innerHTML assignment - XSS vulnerability"),
            (r'dangerouslySetInnerHTML\s*=', "dangerouslySetInnerHTML usage - XSS risk"),
            (r'document\.write\s*\(', "document.write usage - XSS and performance issues"),
            (r'eval\s*\(', "eval() usage - code injection vulnerability"),
            (r'new\s+Function\s*\(', "new Function() - similar risks to eval()"),
        ]
        
        for pattern, msg in xss_patterns:
            matches = list(re.finditer(pattern, content))
            if matches:
                for match in matches[:2]:  # Report up to 2 instances
                    line_num = content[:match.start()].count('\n') + 1
                    smells.append(CodeSmell(
                        path=path,
                        type="XSS Vulnerability",
                        severity=5,
                        line=line_num,
                        message=msg,
                        suggestion="Use textContent instead of innerHTML, or sanitize HTML with DOMPurify"
                    ))
        
        # SQL Injection (raw query building)
        sql_patterns = [
            (r'query\s*\(\s*[`"\'].*?\$\{', "SQL query with template literal interpolation"),
            (r'execute\s*\(\s*[`"\'].*?\+', "SQL execute with string concatenation"),
            (r'\.raw\s*\(\s*[`"\'].*?\$\{', "Raw SQL query with interpolation"),
        ]
        
        for pattern, msg in sql_patterns:
            matches = list(re.finditer(pattern, content, re.IGNORECASE | re.DOTALL))
            if matches:
                line_num = content[:matches[0].start()].count('\n') + 1
                smells.append(CodeSmell(
                    path=path,
                    type="SQL Injection Risk",
                    severity=5,
                    line=line_num,
                    message=msg,
                    suggestion="Use parameterized queries or prepared statements"
                ))
        
        # Hardcoded Secrets/Credentials
        secret_patterns = [
            (r'(?:api[_-]?key|apikey)\s*[:=]\s*["\'][a-zA-Z0-9_\-]{20,}["\']', "Hardcoded API key"),
            (r'(?:password|passwd|pwd)\s*[:=]\s*["\'][^"\']+["\']', "Hardcoded password"),
            (r'(?:secret|token)\s*[:=]\s*["\'][a-zA-Z0-9_\-]{15,}["\']', "Hardcoded secret/token"),
            (r'Bearer\s+[a-zA-Z0-9_\-\.]+', "Hardcoded Bearer token"),
            (r'(?:aws_access_key_id|aws_secret)\s*[:=]', "Hardcoded AWS credentials"),
            (r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----', "Private key in code"),
        ]
        
        for pattern, msg in secret_patterns:
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            if matches:
                line_num = content[:matches[0].start()].count('\n') + 1
                smells.append(CodeSmell(
                    path=path,
                    type="Hardcoded Credentials",
                    severity=5,
                    line=line_num,
                    message=msg,
                    suggestion="Use environment variables, secrets manager, or .env files (gitignored)"
                ))
        
        # Insecure HTTP usage
        http_insecure = re.findall(r'["\']http://(?!localhost|127\.0\.0\.1)[^"\']+["\']', content)
        if http_insecure:
            smells.append(CodeSmell(
                path=path,
                type="Insecure HTTP",
                severity=4,
                line=1,
                message=f"Found {len(http_insecure)} insecure HTTP URLs (non-localhost)",
                suggestion="Use HTTPS for all external URLs"
            ))
        
        # ===== PERFORMANCE ISSUES (Severity 4-5) =====
        
        # Sync operations in browser/Node
        sync_patterns = [
            (r'fs\.(?:readFileSync|writeFileSync|appendFileSync)', "Synchronous file I/O blocks event loop"),
            (r'execSync\s*\(', "Synchronous exec blocks event loop"),
            (r'spawnSync\s*\(', "Synchronous spawn blocks event loop"),
        ]
        
        for pattern, msg in sync_patterns:
            matches = list(re.finditer(pattern, content))
            if matches:
                line_num = content[:matches[0].start()].count('\n') + 1
                smells.append(CodeSmell(
                    path=path,
                    type="Blocking I/O",
                    severity=4,
                    line=line_num,
                    message=msg,
                    suggestion="Use async versions: readFile, writeFile, exec, spawn"
                ))
        
        # N+1 Query Pattern (fetching in loops)
        loop_fetch_pattern = r'(?:for|while|\.forEach|\.map)\s*\([^)]*\)\s*(?:\{[^}]*|=>[^}]*?)(?:fetch|axios|\.get|\.post|\.query|\.findOne|\.find)\s*\('
        if re.search(loop_fetch_pattern, content, re.DOTALL):
            smells.append(CodeSmell(
                path=path,
                type="N+1 Query Pattern",
                severity=5,
                line=1,
                message="Database/API call inside loop - N+1 performance problem",
                suggestion="Batch queries using Promise.all(), or fetch all data before the loop"
            ))
        
        # Memory Leak: Unbounded array growth
        unbounded_push = re.findall(r'(?:while\s*\(true\)|setInterval)\s*(?:\{[^}]*|[^{]*)\.push\s*\(', content, re.DOTALL)
        if unbounded_push:
            smells.append(CodeSmell(
                path=path,
                type="Memory Leak Risk",
                severity=5,
                line=1,
                message="Unbounded array growth in infinite loop/interval",
                suggestion="Limit array size or use circular buffer pattern"
            ))
        
        # Missing cleanup for intervals/timeouts
        set_interval = len(re.findall(r'setInterval\s*\(', content))
        clear_interval = len(re.findall(r'clearInterval\s*\(', content))
        if set_interval > clear_interval + 1:
            smells.append(CodeSmell(
                path=path,
                type="Interval Leak",
                severity=4,
                line=1,
                message=f"Found {set_interval} setInterval but only {clear_interval} clearInterval",
                suggestion="Store interval ID and clear in cleanup (useEffect return, componentWillUnmount)"
            ))
        
        # Event listener leaks
        add_listeners = len(re.findall(r'addEventListener\s*\(', content))
        remove_listeners = len(re.findall(r'removeEventListener\s*\(', content))
        if add_listeners > remove_listeners + 2:
            smells.append(CodeSmell(
                path=path,
                type="Event Listener Leak",
                severity=4,
                line=1,
                message=f"Found {add_listeners} addEventListener but only {remove_listeners} removeEventListener",
                suggestion="Clean up listeners in useEffect cleanup or componentWillUnmount"
            ))
        
        # Large bundle imports
        large_imports = [
            (r'import\s+\w+\s+from\s+["\']lodash["\']', "Full lodash import (~70KB)"),
            (r'import\s+\w+\s+from\s+["\']moment["\']', "moment.js import (~290KB) - use date-fns or dayjs"),
            (r'import\s+\*\s+as\s+\w+\s+from', "Namespace import prevents tree-shaking"),
        ]
        
        for pattern, msg in large_imports:
            matches = list(re.finditer(pattern, content))
            if matches:
                line_num = content[:matches[0].start()].count('\n') + 1
                smells.append(CodeSmell(
                    path=path,
                    type="Large Bundle Import",
                    severity=3,
                    line=line_num,
                    message=msg,
                    suggestion="Use named imports: import { specific } from 'library'"
                ))
        
        # ===== REACT-SPECIFIC ISSUES =====
        
        if '.jsx' in path or '.tsx' in path or 'react' in content.lower():
            # useEffect missing dependencies
            use_effect_pattern = r'useEffect\s*\(\s*\(\)\s*=>\s*{[^}]*}\s*,\s*\[\s*\]\s*\)'
            effects_with_empty_deps = re.findall(use_effect_pattern, content, re.DOTALL)
            for effect in effects_with_empty_deps:
                if re.search(r'\b(?:props\.|state\.|\w+(?:State|Props))\b', effect):
                    smells.append(CodeSmell(
                        path=path,
                        type="Missing Dependencies",
                        severity=4,
                        line=1,
                        message="useEffect with empty deps array uses external variables",
                        suggestion="Add used variables to dependency array or use useCallback"
                    ))
                    break
            
            # State updates without cleanup
            if re.search(r'useEffect\s*\(\s*\(\)\s*=>\s*{[^}]*set\w+\s*\([^}]*}\s*,', content) and \
               not re.search(r'return\s*\(\s*\)\s*=>', content):
                smells.append(CodeSmell(
                    path=path,
                    type="State Update Without Cleanup",
                    severity=4,
                    line=1,
                    message="useEffect sets state but has no cleanup - may cause memory leak",
                    suggestion="Return cleanup function: return () => { /* cleanup */ }"
                ))
            
            # Inline object/array creation in JSX props
            inline_objects = len(re.findall(r'(?:style|className|options)=\{\{[^}]+\}\}', content))
            if inline_objects > 5:
                smells.append(CodeSmell(
                    path=path,
                    type="Inline Object Props",
                    severity=3,
                    line=1,
                    message=f"Found {inline_objects} inline object/array props - causes re-renders",
                    suggestion="Move objects outside component or use useMemo"
                ))
            
            # Anonymous functions in JSX
            anon_handlers = len(re.findall(r'on\w+=\{(?:\([^)]*\)\s*=>|\(\s*\)\s*=>|function\s*\()', content))
            if anon_handlers > 5:
                smells.append(CodeSmell(
                    path=path,
                    type="Anonymous Handlers",
                    severity=3,
                    line=1,
                    message=f"Found {anon_handlers} anonymous functions in event handlers",
                    suggestion="Use useCallback for event handlers to prevent unnecessary re-renders"
                ))
        
        # ===== ASYNC/AWAIT ISSUES =====
        
        # Unhandled promise rejections
        async_without_catch = len(re.findall(r'(?:async\s+function|\basync\s*\([^)]*\)\s*=>)[^}]*await\s+[^}]*}', content, re.DOTALL))
        try_catch_count = len(re.findall(r'try\s*{', content))
        catch_count = len(re.findall(r'\.catch\s*\(', content))
        
        if async_without_catch > 0 and (try_catch_count + catch_count) < async_without_catch:
            smells.append(CodeSmell(
                path=path,
                type="Unhandled Promise Rejection",
                severity=4,
                line=1,
                message="Async functions without proper error handling",
                suggestion="Wrap await calls in try-catch or add .catch() handlers"
            ))
        
        # Await in loop (sequential instead of parallel)
        await_in_loop = re.search(r'(?:for|while)\s*\([^)]*\)\s*{[^}]*await\s+', content, re.DOTALL)
        if await_in_loop and 'Promise.all' not in content:
            smells.append(CodeSmell(
                path=path,
                type="Sequential Await",
                severity=4,
                line=1,
                message="Await inside loop executes sequentially instead of in parallel",
                suggestion="Use Promise.all() with map to parallelize: await Promise.all(items.map(async i => ...))"
            ))
        
        # ===== CODE QUALITY ISSUES =====
        
        # Deeply nested callbacks
        max_callback_depth = 0
        current_callback_depth = 0
        
        for line in lines:
            callback_starts = len(re.findall(r'function\s*\([^)]*\)\s*{|=>\s*{|\(\s*\([^)]*\)\s*=>\s*{', line))
            callback_ends = line.count('});') + line.count('})')
            
            current_callback_depth += callback_starts
            current_callback_depth = max(0, current_callback_depth - callback_ends)
            max_callback_depth = max(max_callback_depth, current_callback_depth)
        
        if max_callback_depth >= 4:
            smells.append(CodeSmell(
                path=path,
                type="Callback Hell",
                severity=4,
                line=1,
                message=f"Deep callback nesting (depth: {max_callback_depth})",
                suggestion="Refactor using async/await or Promises to flatten structure"
            ))
        
        # Long functions
        func_pattern = re.compile(
            r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)',
            re.MULTILINE
        )
        
        for match in func_pattern.finditer(content):
            func_name = match.group(1) or match.group(2) or 'anonymous'
            start_pos = match.end()
            
            brace_count = 1
            end_pos = start_pos
            for i, char in enumerate(content[start_pos:], start_pos):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = i
                        break
            
            func_lines = content[start_pos:end_pos].count('\n')
            line_num = content[:match.start()].count('\n') + 1
            
            # Only flag extremely long functions (300+ lines for JS/React components)
            # React components and pages are naturally longer
            is_test_file = any(x in path.lower() for x in ['test', 'spec', 'mock', '__test__'])
            is_page_or_component = any(x in path.lower() for x in ['page', 'component', 'view', 'screen'])
            
            threshold = 500 if is_page_or_component else 300
            if func_lines > threshold and not is_test_file:
                smells.append(CodeSmell(
                    path=path,
                    type="Long Function",
                    severity=2,  # Low severity - informational only
                    line=line_num,
                    message=f"Function '{func_name}' has ~{func_lines} lines - quite large",
                    suggestion="Optional: Consider breaking into smaller functions if it improves readability"
                ))
        
        # Empty catch blocks
        empty_catch = re.findall(r'catch\s*\([^)]*\)\s*{\s*}', content)
        if empty_catch:
            smells.append(CodeSmell(
                path=path,
                type="Empty Catch Block",
                severity=4,
                line=1,
                message=f"Found {len(empty_catch)} empty catch blocks",
                suggestion="Log errors or handle them appropriately"
            ))
        
        # TypeScript 'any' abuse
        if path.endswith('.ts') or path.endswith('.tsx'):
            any_count = len(re.findall(r':\s*any\b', content))
            if any_count > 5:
                smells.append(CodeSmell(
                    path=path,
                    type="Excessive Any Types",
                    severity=4,
                    line=1,
                    message=f"Found {any_count} uses of 'any' type - defeats TypeScript benefits",
                    suggestion="Define proper interfaces/types or use 'unknown' for truly unknown types"
                ))
        
        # ===== MAINTENANCE ISSUES =====
        
        # Console statements
        console_matches = len(re.findall(r'console\.(log|warn|error|debug|info)', content))
        if console_matches > 5:
            smells.append(CodeSmell(
                path=path,
                type="Debug Statements",
                severity=2,
                line=1,
                message=f"Found {console_matches} console statements",
                suggestion="Remove debug statements or use proper logging library"
            ))
        
        # TODO/FIXME
        todo_matches = len(re.findall(r'(TODO|FIXME|HACK|XXX|BUG)', content, re.IGNORECASE))
        if todo_matches > 0:
            smells.append(CodeSmell(
                path=path,
                type="Unresolved TODOs",
                severity=2,
                line=1,
                message=f"Found {todo_matches} TODO/FIXME comments",
                suggestion="Address or create tickets for tracking"
            ))
        
        # Long file
        if loc > 500:
            smells.append(CodeSmell(
                path=path,
                type="Long File",
                severity=3 if loc > 800 else 2,
                line=1,
                message=f"File has {loc} lines",
                suggestion="Split into multiple modules by responsibility"
            ))
        
        return smells


class RepoAnalyzer:
    """Main repository analyzer that clones and analyzes GitHub repositories."""
    
    SUPPORTED_EXTENSIONS = {
        '.py': PythonAnalyzer,
        '.js': JavaScriptAnalyzer,
        '.jsx': JavaScriptAnalyzer,
        '.ts': JavaScriptAnalyzer,
        '.tsx': JavaScriptAnalyzer,
    }
    
    IGNORED_DIRS = {
        'node_modules', '.git', '__pycache__', '.venv', 'venv', 
        'env', '.env', 'dist', 'build', '.next', 'coverage',
        '.pytest_cache', '.mypy_cache', 'eggs', '*.egg-info'
    }
    
    def __init__(self):
        self.temp_dir: Optional[Path] = None
        
    async def analyze_github_repo(self, github_url: str) -> Dict[str, Any]:
        """Clone and analyze a GitHub repository."""
        try:
            # Create temp directory path (but don't create it - git clone will do that)
            temp_base = Path(tempfile.gettempdir())
            self.temp_dir = temp_base / f"codesensex_{os.urandom(8).hex()}"
            
            print(f"🔍 Cloning {github_url} to {self.temp_dir}...", flush=True)
            
            # Clone repository
            clone_success = await self._clone_repo(github_url)
            if not clone_success:
                print(f"❌ Failed to clone {github_url}", flush=True)
                return {"error": "Failed to clone repository", "metrics": [], "risks": [], "smells": []}
            
            print(f"✅ Clone successful, analyzing files...", flush=True)
            
            # Find all analyzable files
            all_metrics: List[FileMetrics] = []
            all_smells: List[CodeSmell] = []
            
            for file_path in self._find_files():
                ext = file_path.suffix.lower()
                if ext in self.SUPPORTED_EXTENSIONS:
                    analyzer = self.SUPPORTED_EXTENSIONS[ext]
                    relative_path = str(file_path.relative_to(self.temp_dir))
                    
                    metrics, smells = analyzer.analyze_file(file_path, relative_path)
                    if metrics:
                        all_metrics.append(metrics)
                    all_smells.extend(smells)
            
            # Calculate risk scores
            risks = self._calculate_risks(all_metrics, all_smells)
            
            return {
                "metrics": [asdict(m) for m in all_metrics],
                "risks": [asdict(r) for r in risks],
                "smells": [asdict(s) for s in all_smells],
                "summary": {
                    "total_files": len(all_metrics),
                    "total_loc": sum(m.loc for m in all_metrics),
                    "total_smells": len(all_smells),
                    "languages": list(set(m.language for m in all_metrics))
                }
            }
            
        finally:
            # Cleanup
            if self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    async def _clone_repo(self, github_url: str) -> bool:
        """Clone a GitHub repository."""
        try:
            # Clean URL
            url = github_url.strip()
            if not url.endswith('.git'):
                url = url.rstrip('/') + '.git'
            
            print(f"  Running: git clone --depth 1 {url} {self.temp_dir}", flush=True)
            
            # Clone with depth=1 for speed
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', url, str(self.temp_dir)],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                print(f"  Git stderr: {result.stderr}", flush=True)
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("  Clone timed out after 120 seconds", flush=True)
            return False
        except FileNotFoundError:
            print("  Error: git command not found. Make sure git is installed.", flush=True)
            return False
        except Exception as e:
            print(f"  Clone error: {e}", flush=True)
            return False
    
    def _find_files(self) -> List[Path]:
        """Find all analyzable files in the repository."""
        files = []
        
        for file_path in self.temp_dir.rglob('*'):
            if not file_path.is_file():
                continue
                
            # Skip ignored directories
            if any(ignored in file_path.parts for ignored in self.IGNORED_DIRS):
                continue
                
            # Only include supported extensions
            if file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                files.append(file_path)
        
        return files
    
    def _calculate_risks(self, metrics: List[FileMetrics], smells: List[CodeSmell]) -> List[RiskScore]:
        """Calculate risk scores for each file based on metrics and smells."""
        risks = []
        
        # Group smells by file
        smells_by_file: Dict[str, List[CodeSmell]] = {}
        for smell in smells:
            if smell.path not in smells_by_file:
                smells_by_file[smell.path] = []
            smells_by_file[smell.path].append(smell)
        
        for m in metrics:
            # Calculate risk score based on multiple weighted factors
            score = 0
            top_features = []
            
            file_smells = smells_by_file.get(m.path, [])
            
            # ===== CRITICAL FACTORS (highest weight) =====
            
            # High cyclomatic complexity - major bug predictor (0-25 points)
            if m.cyclomatic_max > 25:
                score += 25
                top_features.append("extreme_complexity")
            elif m.cyclomatic_max > 15:
                score += 20
                top_features.append("high_complexity")
            elif m.cyclomatic_max > 10:
                score += 12
                top_features.append("moderate_complexity")
            
            # Critical code smells (0-25 points)
            critical_smells = [s for s in file_smells if s.severity >= 4]
            critical_types = set(s.type for s in critical_smells)
            
            # Security vulnerabilities get highest priority
            security_smells = {'SQL Injection Risk', 'Hardcoded Secret', 'Database Credentials Exposed',
                             'API Key Exposed', 'AWS Credentials Exposed', 'Private Key Exposed',
                             'JWT Token Hardcoded', 'Code Injection Risk', 'XSS Vulnerability'}
            security_count = sum(1 for s in critical_smells if s.type in security_smells)
            
            # Weight certain smell types higher - Long Function is NOT high risk
            high_risk_smells = {'Callback Hell', 'Empty Catch Block', 'Potential Memory Leak', 
                               'High Complexity', 'God Class', 'N+1 Query Problem',
                               'Blocking Call in Async', 'Resource Leak Risk'}
            # Long Function is excluded - it's just style, not a bug risk
            high_risk_count = sum(1 for s in critical_smells if s.type in high_risk_smells)
            
            # Security issues add maximum risk
            if security_count > 0:
                score += 30  # Security issues are critical
                top_features.append(f"security_vulnerabilities_{security_count}")
            elif high_risk_count >= 3:
                score += 25
                top_features.append("multiple_critical_issues")
            elif high_risk_count >= 2:
                score += 20
                top_features.append("critical_issues")
            elif high_risk_count >= 1:
                score += 15
                top_features.append("has_critical_issue")
            
            # ===== IMPORTANT FACTORS (medium weight) =====
            
            # Deep nesting - cognitive complexity (0-15 points)
            if m.nesting_max > 7:
                score += 15
                top_features.append("deep_nesting")
            elif m.nesting_max > 5:
                score += 10
                top_features.append("nesting_depth")
            elif m.nesting_max > 4:
                score += 5
            
            # Function count (too many functions = hard to maintain) (0-10 points)
            if m.fn_count > 30:
                score += 10
                top_features.append("too_many_functions")
            elif m.fn_count > 20:
                score += 5
            
            # Low comment ratio (potential documentation debt) (0-5 points)
            if m.sloc > 100 and m.comment_ratio < 0.02:
                score += 5
                top_features.append("poor_documentation")
            
            # ===== SECONDARY FACTORS (lower weight) =====
            
            # Medium severity smells (0-10 points)
            medium_smells = sum(1 for s in file_smells if s.severity == 3)
            if medium_smells >= 5:
                score += 10
            elif medium_smells >= 3:
                score += 5
            
            # File size - only counts if very large (0-10 points)
            if m.loc > 800:
                score += 10
                top_features.append("very_large_file")
            elif m.loc > 500:
                score += 5
            
            # Low severity smells (0-5 points)
            low_smells = sum(1 for s in file_smells if s.severity <= 2)
            if low_smells >= 8:
                score += 5
            
            # ===== BONUS RISK INDICATORS =====
            
            # Multiple smell types indicate systemic issues
            smell_types = set(s.type for s in file_smells)
            if len(smell_types) >= 5:
                score += 10
                top_features.append("multiple_issue_types")
            elif len(smell_types) >= 3:
                score += 5
            
            # Determine tier based on score
            if score >= 70:
                tier = "Critical"
            elif score >= 50:
                tier = "High"
            elif score >= 30:
                tier = "Medium"
            else:
                tier = "Low"
            
            risks.append(RiskScore(
                path=m.path,
                risk_score=min(score, 100),
                tier=tier,
                top_features=top_features[:4]  # Top 4 contributing factors
            ))
        
        # Sort by risk score descending
        risks.sort(key=lambda r: r.risk_score, reverse=True)
        
        return risks


# Singleton instance
repo_analyzer = RepoAnalyzer()
