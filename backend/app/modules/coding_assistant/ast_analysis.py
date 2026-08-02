"""AST Parsing skill: structural analysis of Python source using the
standard library `ast` module — no LLM call, no external dependency."""

import ast

from app.modules.coding_assistant.schemas import AstAnalysis, ClassInfo, FunctionInfo

# Node types that add a branch to cyclomatic complexity — a rough, standard
# proxy (if/for/while/except/boolop each add one path).
_BRANCH_NODES = (
    ast.If,
    ast.For,
    ast.While,
    ast.ExceptHandler,
    ast.With,
    ast.Assert,
    ast.BoolOp,
)


def _function_info(node: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionInfo:
    return FunctionInfo(
        name=node.name,
        args=[a.arg for a in node.args.args],
        docstring=ast.get_docstring(node),
        lineno=node.lineno,
        is_async=isinstance(node, ast.AsyncFunctionDef),
    )


def _class_info(node: ast.ClassDef) -> ClassInfo:
    methods = [
        n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    bases = [ast.unparse(b) for b in node.bases]
    return ClassInfo(
        name=node.name,
        bases=bases,
        methods=methods,
        docstring=ast.get_docstring(node),
        lineno=node.lineno,
    )


def analyze(source: str) -> AstAnalysis:
    tree = ast.parse(source)

    imports: list[str] = []
    functions: list[FunctionInfo] = []
    classes: list[ClassInfo] = []
    complexity = 1  # baseline path

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports.extend(f"{module}.{alias.name}" for alias in node.names)
        elif isinstance(node, _BRANCH_NODES):
            complexity += 1

    # Top-level (and nested, via walk) function/class defs — walk() already
    # recurses, so this also picks up methods and nested functions.
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(_function_info(node))
        elif isinstance(node, ast.ClassDef):
            classes.append(_class_info(node))

    return AstAnalysis(
        imports=sorted(set(imports)),
        functions=functions,
        classes=classes,
        line_count=len(source.splitlines()),
        approx_complexity=complexity,
    )
