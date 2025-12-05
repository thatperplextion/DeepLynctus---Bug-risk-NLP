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
    'insecure_random': [
        r'random\.random\s*\(',  # Non-cryptographic random
        r'random\.randint\s*\(',
        r'Math\.random\s*\(',
    ],
    'path_traversal': [
        r'open\s*\([^)]*\+[^)]*\)',  # Path concatenation without validation
        r'os\.path\.join\s*\([^)]*request',  # User input in path
    ],
    'command_injection': [
        r'os\.system\s*\([^)]*\+',
        r'subprocess\.(?:call|run|Popen)\s*\([^)]*shell\s*=\s*True',
        r'eval\s*\(',
        r'exec\s*\(',
    ],
    'xss_vulnerable': [
        r'innerHTML\s*=',
        r'document\.write\s*\(',
        r'dangerouslySetInnerHTML',
    ],
}

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
        """Detect code smells in Python code."""
        smells = []
        content = '\n'.join(lines)
        loc = len(lines)
        
        # ===== FUNCTION-LEVEL SMELLS =====
        for func in functions:
            func_name = func.name
            func_lines = func.end_lineno - func.lineno + 1 if hasattr(func, 'end_lineno') else 50
            
            # Long function
            if func_lines > 50:
                severity = 5 if func_lines > 100 else 4 if func_lines > 75 else 3
                smells.append(CodeSmell(
                    path=path,
                    type="Long Function",
                    severity=severity,
                    line=func.lineno,
                    message=f"Function '{func_name}' has {func_lines} lines (recommended: <50)",
                    suggestion=f"Consider breaking '{func_name}' into smaller functions"
                ))
            
            # High complexity
            visitor = CyclomaticComplexityVisitor()
            visitor.visit(func)
            if visitor.complexity > 10:
                severity = 5 if visitor.complexity > 20 else 4 if visitor.complexity > 15 else 3
                smells.append(CodeSmell(
                    path=path,
                    type="High Complexity",
                    severity=severity,
                    line=func.lineno,
                    message=f"Function '{func_name}' has cyclomatic complexity of {visitor.complexity} (recommended: <10)",
                    suggestion="Reduce branching by extracting conditions into helper functions"
                ))
            
            # Too many parameters
            num_args = len(func.args.args) + len(func.args.posonlyargs) + len(func.args.kwonlyargs)
            if num_args > 5:
                severity = 4 if num_args > 7 else 3
                smells.append(CodeSmell(
                    path=path,
                    type="Too Many Parameters",
                    severity=severity,
                    line=func.lineno,
                    message=f"Function '{func_name}' has {num_args} parameters (recommended: ≤5)",
                    suggestion="Consider using a data class or dictionary to group related parameters"
                ))
            
            # Missing docstring for public functions
            if not func_name.startswith('_') and not ast.get_docstring(func):
                smells.append(CodeSmell(
                    path=path,
                    type="Missing Docstring",
                    severity=2,
                    line=func.lineno,
                    message=f"Public function '{func_name}' lacks a docstring",
                    suggestion="Add a docstring describing purpose, parameters, and return value"
                ))
        
        # ===== EXCEPTION HANDLING SMELLS =====
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                # Bare except clause (catches everything including KeyboardInterrupt)
                if node.type is None:
                    smells.append(CodeSmell(
                        path=path,
                        type="Bare Except",
                        severity=4,
                        line=node.lineno,
                        message="Bare 'except:' clause catches all exceptions including system exits",
                        suggestion="Specify exception types: 'except Exception:' or more specific"
                    ))
                
                # Check for pass-only except blocks (swallowing exceptions)
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    smells.append(CodeSmell(
                        path=path,
                        type="Swallowed Exception",
                        severity=4,
                        line=node.lineno,
                        message="Exception is silently swallowed with 'pass'",
                        suggestion="Log the exception or re-raise after handling"
                    ))
        
        # ===== STRUCTURAL SMELLS =====
        
        # Deep nesting
        nesting_visitor = NestingVisitor()
        nesting_visitor.visit(tree)
        if nesting_visitor.max_depth > 4:
            severity = 5 if nesting_visitor.max_depth > 6 else 4 if nesting_visitor.max_depth > 5 else 3
            smells.append(CodeSmell(
                path=path,
                type="Deep Nesting",
                severity=severity,
                line=1,
                message=f"Maximum nesting depth is {nesting_visitor.max_depth} (recommended: ≤4)",
                suggestion="Use early returns, guard clauses, or extract nested logic into functions"
            ))
        
        # God class (too many methods or attributes)
        for cls in classes:
            methods = [node for node in ast.walk(cls) 
                      if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
            
            # Count instance attributes
            attrs = set()
            for node in ast.walk(cls):
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == 'self':
                    attrs.add(node.attr)
            
            if len(methods) > 20:
                severity = 4 if len(methods) > 30 else 3
                smells.append(CodeSmell(
                    path=path,
                    type="God Class",
                    severity=severity,
                    line=cls.lineno,
                    message=f"Class '{cls.name}' has {len(methods)} methods (recommended: ≤20)",
                    suggestion="Consider splitting into smaller, focused classes using composition"
                ))
            
            if len(attrs) > 15:
                smells.append(CodeSmell(
                    path=path,
                    type="Data Clump",
                    severity=3,
                    line=cls.lineno,
                    message=f"Class '{cls.name}' has {len(attrs)} attributes (recommended: ≤15)",
                    suggestion="Group related attributes into separate data classes"
                ))
        
        # ===== MAGIC VALUES AND CONSTANTS =====
        
        # Magic numbers (large numeric literals not in obvious patterns)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                val = node.value
                # Skip common values like 0, 1, 2, -1, 100, etc.
                if isinstance(val, int) and abs(val) > 100 and val not in {1000, 10000, 100000}:
                    line_content = lines[node.lineno - 1] if node.lineno <= len(lines) else ''
                    # Skip if it's in a constant assignment
                    if not re.search(r'^[A-Z_]+\s*=', line_content.strip()):
                        smells.append(CodeSmell(
                            path=path,
                            type="Magic Number",
                            severity=3,
                            line=node.lineno,
                            message=f"Magic number {val} found - consider using a named constant",
                            suggestion="Extract to a named constant: MY_CONSTANT = " + str(val)
                        ))
                        break  # Only report once per file
        
        # ===== CODE MAINTENANCE SMELLS =====
        
        # TODO/FIXME/HACK comments
        todo_count = 0
        first_todo_line = None
        for i, line in enumerate(lines, 1):
            if re.search(r'#\s*(TODO|FIXME|HACK|XXX):', line, re.IGNORECASE):
                todo_count += 1
                if first_todo_line is None:
                    first_todo_line = i
        
        if todo_count > 0:
            smells.append(CodeSmell(
                path=path,
                type="Unresolved TODOs",
                severity=2 if todo_count < 5 else 3,
                line=first_todo_line or 1,
                message=f"Found {todo_count} unresolved TODO/FIXME comments",
                suggestion="Review and address or create tickets for tracking"
            ))
        
        # Commented out code (lines starting with # followed by code-like patterns)
        commented_code_count = 0
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#') and not stripped.startswith('# '):
                # Check if it looks like commented code
                after_hash = stripped[1:].strip()
                if re.match(r'^(def |class |import |from |if |for |while |return |self\.)', after_hash):
                    commented_code_count += 1
        
        if commented_code_count >= 3:
            smells.append(CodeSmell(
                path=path,
                type="Commented Code",
                severity=2,
                line=1,
                message=f"Found {commented_code_count} lines of commented-out code",
                suggestion="Remove dead code - use version control for history"
            ))
        
        # Debug print statements
        print_count = sum(1 for line in lines if re.search(r'\bprint\s*\(', line) and 
                         not line.strip().startswith('#'))
        if print_count > 5:
            smells.append(CodeSmell(
                path=path,
                type="Debug Code",
                severity=2,
                line=1,
                message=f"Found {print_count} print statements - likely debug code",
                suggestion="Use logging module instead of print for production code"
            ))
        
        # ===== IMPORT SMELLS =====
        
        # Star imports
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and any(alias.name == '*' for alias in node.names):
                smells.append(CodeSmell(
                    path=path,
                    type="Star Import",
                    severity=3,
                    line=node.lineno,
                    message=f"Star import from '{node.module}' pollutes namespace",
                    suggestion="Import specific names instead of using 'from module import *'"
                ))
        
        # ===== FILE-LEVEL SMELLS =====
        
        # Very long file (only flag if truly excessive)
        if loc > 500:
            severity = 3 if loc > 800 else 2
            smells.append(CodeSmell(
                path=path,
                type="Long File",
                severity=severity,
                line=1,
                message=f"File has {loc} lines (recommended: <500)",
                suggestion="Consider splitting into multiple modules by responsibility"
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
        """Detect code smells in JavaScript/TypeScript."""
        smells = []
        loc = len(lines)
        
        # ===== HIGH SEVERITY ISSUES (4-5) =====
        
        # Deeply nested callbacks - track actual brace nesting within callback patterns
        max_callback_depth = 0
        current_callback_depth = 0
        in_callback = False
        
        for line in lines:
            stripped = line.strip()
            # Detect callback pattern starts
            callback_starts = len(re.findall(r'function\s*\([^)]*\)\s*{|=>\s*{|\(\s*\([^)]*\)\s*=>\s*{', line))
            callback_ends = stripped.count('});') + stripped.count('})')
            
            current_callback_depth += callback_starts
            current_callback_depth = max(0, current_callback_depth - callback_ends)
            max_callback_depth = max(max_callback_depth, current_callback_depth)
        
        # Only report if genuinely deep (4+ levels is unusual)
        if max_callback_depth >= 4:
            smells.append(CodeSmell(
                path=path,
                type="Callback Hell",
                severity=5 if max_callback_depth >= 6 else 4,
                line=1,
                message=f"Deep callback nesting detected (depth: {max_callback_depth})",
                suggestion="Refactor using async/await or Promises to flatten callback structure"
            ))
        
        # Large functions - find function boundaries more accurately
        func_pattern = re.compile(
            r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>|(?:async\s+)?(\w+)\s*\([^)]*\)\s*{)',
            re.MULTILINE
        )
        
        for match in func_pattern.finditer(content):
            func_name = match.group(1) or match.group(2) or match.group(3) or 'anonymous'
            start_pos = match.end()
            
            # Find matching closing brace
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
            
            if func_lines > 80:
                smells.append(CodeSmell(
                    path=path,
                    type="Long Function",
                    severity=5 if func_lines > 150 else 4,
                    line=line_num,
                    message=f"Function '{func_name}' has approximately {func_lines} lines (recommended: <50)",
                    suggestion="Break down into smaller, single-responsibility functions"
                ))
        
        # Complex ternary expressions (nested ternaries)
        nested_ternary_count = len(re.findall(r'\?[^?:]+\?', content))
        if nested_ternary_count > 0:
            smells.append(CodeSmell(
                path=path,
                type="Nested Ternary",
                severity=4,
                line=1,
                message=f"Found {nested_ternary_count} nested ternary expression(s)",
                suggestion="Replace nested ternaries with if-else statements or helper functions"
            ))
        
        # Magic numbers - look for large numeric literals not in obvious constant patterns
        magic_numbers = re.findall(r'(?<!["\'\w])(?:[2-9]\d{2,}|1\d{3,})(?!["\'\w])', content)
        # Filter out common values like array indices, pixel values, etc.
        significant_magic = [n for n in magic_numbers if int(n) not in {100, 200, 300, 400, 500, 1000, 2000}]
        if len(significant_magic) > 5:
            smells.append(CodeSmell(
                path=path,
                type="Magic Numbers",
                severity=3,
                line=1,
                message=f"Found {len(significant_magic)} potential magic numbers",
                suggestion="Extract magic numbers to named constants for better readability"
            ))
        
        # ===== MEDIUM SEVERITY ISSUES (3) =====
        
        # Empty catch blocks
        empty_catch = re.findall(r'catch\s*\([^)]*\)\s*{\s*}', content)
        if empty_catch:
            smells.append(CodeSmell(
                path=path,
                type="Empty Catch Block",
                severity=4,
                line=1,
                message=f"Found {len(empty_catch)} empty catch blocks",
                suggestion="Handle errors properly or log them for debugging"
            ))
        
        # Potential memory leaks (event listeners without cleanup)
        add_listeners = len(re.findall(r'addEventListener\s*\(', content))
        remove_listeners = len(re.findall(r'removeEventListener\s*\(', content))
        if add_listeners > remove_listeners + 2:
            smells.append(CodeSmell(
                path=path,
                type="Potential Memory Leak",
                severity=4,
                line=1,
                message=f"Found {add_listeners} addEventListener calls but only {remove_listeners} removeEventListener",
                suggestion="Ensure all event listeners are properly cleaned up in useEffect cleanup or componentWillUnmount"
            ))
        
        # Duplicate string literals
        string_literals = re.findall(r'["\']([^"\']{10,})["\']', content)
        from collections import Counter
        string_counts = Counter(string_literals)
        duplicates = [(s, c) for s, c in string_counts.items() if c >= 3]
        if duplicates:
            smells.append(CodeSmell(
                path=path,
                type="Duplicate Strings",
                severity=3,
                line=1,
                message=f"Found {len(duplicates)} string literals repeated 3+ times",
                suggestion="Extract repeated strings to constants"
            ))
        
        # Excessive use of any type (TypeScript)
        if path.endswith('.ts') or path.endswith('.tsx'):
            any_count = len(re.findall(r':\s*any\b', content))
            if any_count > 3:
                smells.append(CodeSmell(
                    path=path,
                    type="Excessive Any Type",
                    severity=3,
                    line=1,
                    message=f"Found {any_count} uses of 'any' type",
                    suggestion="Replace 'any' with proper type definitions for type safety"
                ))
        
        # Commented out code
        commented_code = len(re.findall(r'//\s*(const|let|var|function|if|for|while|return)\s+', content))
        if commented_code > 5:
            smells.append(CodeSmell(
                path=path,
                type="Commented Code",
                severity=2,
                line=1,
                message=f"Found approximately {commented_code} lines of commented-out code",
                suggestion="Remove commented code - use version control for history"
            ))
        
        # ===== LOW SEVERITY ISSUES (1-2) =====
        
        # Console.log statements (likely debug code)
        console_matches = list(re.finditer(r'console\.(log|warn|error|debug|info)', content))
        if len(console_matches) > 3:
            smells.append(CodeSmell(
                path=path,
                type="Debug Code",
                severity=2,
                line=1,
                message=f"Found {len(console_matches)} console statements",
                suggestion="Remove debug statements or use proper logging library"
            ))
        
        # TODO/FIXME comments - only add once per file with count
        todo_matches = list(re.finditer(r'(TODO|FIXME|HACK|XXX|BUG)', content, re.IGNORECASE))
        if todo_matches:
            smells.append(CodeSmell(
                path=path,
                type="Unresolved TODOs",
                severity=2,
                line=1,
                message=f"Found {len(todo_matches)} TODO/FIXME comments",
                suggestion="Address or create tickets for unresolved TODOs"
            ))
        
        # Long file (only flag if really long)
        if len(lines) > 500:
            smells.append(CodeSmell(
                path=path,
                type="Very Long File",
                severity=3 if len(lines) > 800 else 2,
                line=1,
                message=f"File has {len(lines)} lines (recommended: <400)",
                suggestion="Consider splitting into multiple modules by responsibility"
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
            
            # Weight certain smell types higher
            high_risk_smells = {'Callback Hell', 'Empty Catch Block', 'Potential Memory Leak', 
                               'High Complexity', 'Long Function', 'God Class'}
            high_risk_count = sum(1 for s in critical_smells if s.type in high_risk_smells)
            
            if high_risk_count >= 3:
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
