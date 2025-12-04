import ast

class PythonParser:
    @staticmethod
    def analyze(code: str) -> dict:
        tree = ast.parse(code)
        functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        loc = len(code.splitlines())
        avg_fn_len = loc / max(len(functions), 1)
        return {"loc": loc, "avg_fn_len": avg_fn_len, "cyclomatic_max": len(functions)}
