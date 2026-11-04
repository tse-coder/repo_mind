"""
Python AST analysis engine for RepoMind (Tier 1 Code Intelligence).

Extracts symbols (functions, methods, classes, variables), imports,
and function call chains using Python's standard `ast` module.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SymbolInfo:
    """Represents a code symbol (class, function, method)."""

    name: str
    kind: str  # "class" | "function" | "method"
    file_path: str
    start_line: int
    end_line: int
    signature: str = ""
    docstring: str | None = None
    parent: str | None = None


@dataclass
class ImportInfo:
    """Represents an import statement in a file."""

    source_file: str
    module: str
    imported_names: list[str] = field(default_factory=list)
    is_relative: bool = False
    level: int = 0


@dataclass
class CallInfo:
    """Represents a function or method invocation."""

    caller_name: str
    callee_name: str
    file_path: str
    line_number: int


class ASTVisitor(ast.NodeVisitor):
    """Walks the AST of a single file to extract symbols, imports, and calls."""

    def __init__(self, file_path: str, source_code: str):
        self.file_path = file_path
        self.lines = source_code.splitlines()
        self.symbols: list[SymbolInfo] = []
        self.imports: list[ImportInfo] = []
        self.calls: list[CallInfo] = []
        self.scope_stack: list[str] = []

    def _get_signature(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        """Extract a readable signature string."""
        args_list: list[str] = []
        for arg in node.args.args:
            name = arg.arg
            if arg.annotation:
                name += f": {ast.unparse(arg.annotation)}"
            args_list.append(name)
        ret = f" -> {ast.unparse(node.returns)}" if node.returns else ""
        return f"def {node.name}({', '.join(args_list)}){ret}"

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        parent = self.scope_stack[-1] if self.scope_stack else None
        docstring = ast.get_docstring(node)
        bases = [ast.unparse(b) for b in node.bases]
        sig = f"class {node.name}({', '.join(bases)})" if bases else f"class {node.name}"

        self.symbols.append(
            SymbolInfo(
                name=node.name,
                kind="class",
                file_path=self.file_path,
                start_line=node.lineno,
                end_line=getattr(node, "end_lineno", node.lineno),
                signature=sig,
                docstring=docstring,
                parent=parent,
            )
        )

        self.scope_stack.append(node.name)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        self._handle_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
        self._handle_function(node)

    def _handle_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        parent = self.scope_stack[-1] if self.scope_stack else None
        kind = "method" if parent else "function"
        docstring = ast.get_docstring(node)
        sig = self._get_signature(node)

        self.symbols.append(
            SymbolInfo(
                name=node.name,
                kind=kind,
                file_path=self.file_path,
                start_line=node.lineno,
                end_line=getattr(node, "end_lineno", node.lineno),
                signature=sig,
                docstring=docstring,
                parent=parent,
            )
        )

        self.scope_stack.append(node.name)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_Import(self, node: ast.Import) -> Any:
        for alias in node.names:
            self.imports.append(
                ImportInfo(
                    source_file=self.file_path,
                    module=alias.name,
                    imported_names=[alias.asname or alias.name],
                    is_relative=False,
                )
            )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        mod = node.module or ""
        names = [alias.name for alias in node.names]
        self.imports.append(
            ImportInfo(
                source_file=self.file_path,
                module=mod,
                imported_names=names,
                is_relative=node.level > 0,
                level=node.level,
            )
        )

    def visit_Call(self, node: ast.Call) -> Any:
        callee_name = ""
        if isinstance(node.func, ast.Name):
            callee_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            callee_name = node.func.attr

        if callee_name:
            caller = self.scope_stack[-1] if self.scope_stack else "<module>"
            self.calls.append(
                CallInfo(
                    caller_name=caller,
                    callee_name=callee_name,
                    file_path=self.file_path,
                    line_number=node.lineno,
                )
            )
        self.generic_visit(node)


class RepoASTIndex:
    """Indexed collection of symbols, imports, and calls across a repository."""

    def __init__(self, repo_path: str | Path):
        self.repo_path = Path(repo_path).resolve()
        self.symbols: list[SymbolInfo] = []
        self.imports: list[ImportInfo] = []
        self.calls: list[CallInfo] = []
        self._build_index()

    def _build_index(self):
        """Parse all Python files in the repository."""
        for py_file in self.repo_path.rglob("*.py"):
            # Exclude virtual environments and hidden dirs
            parts = py_file.parts
            if any(p.startswith(".") or p in ("venv", "__pycache__", "node_modules") for p in parts):
                continue

            try:
                content = py_file.read_text(encoding="utf-8", errors="replace")
                parsed = ast.parse(content, filename=str(py_file))
                rel_path = str(py_file.relative_to(self.repo_path))
                visitor = ASTVisitor(file_path=rel_path, source_code=content)
                visitor.visit(parsed)

                self.symbols.extend(visitor.symbols)
                self.imports.extend(visitor.imports)
                self.calls.extend(visitor.calls)
            except (SyntaxError, UnicodeDecodeError, OSError):
                # Error-tolerant parsing: syntax error in one file degrades only that file
                continue

    def search_symbols(self, query: str, kind: str | None = None) -> list[SymbolInfo]:
        """Search symbols by name (case-insensitive substring) and optional kind."""
        q = query.lower()
        results: list[SymbolInfo] = []
        for s in self.symbols:
            if kind and s.kind.lower() != kind.lower():
                continue
            if not q or q == "*" or q in s.name.lower():
                results.append(s)
        return results

    def get_symbol(self, symbol_name: str, file_path: str | None = None) -> SymbolInfo | None:
        """Retrieve exact symbol definition."""
        for s in self.symbols:
            if s.name == symbol_name:
                if file_path is None or s.file_path == file_path:
                    return s
        return None

    def find_references(self, symbol_name: str) -> list[CallInfo]:
        """Find calls or usages referencing a specific symbol."""
        return [c for c in self.calls if c.callee_name == symbol_name]

    def get_relationships(self, file_path: str, direction: str = "imports") -> list[ImportInfo]:
        """Get import relationships for a file (imports or imported_by)."""
        rel_path = str(Path(file_path))
        if direction == "imports":
            return [imp for imp in self.imports if imp.source_file == rel_path]
        elif direction == "imported_by":
            # Check what other files import this module/file
            target_stem = Path(file_path).stem
            matches: list[ImportInfo] = []
            for imp in self.imports:
                if imp.source_file != rel_path and (target_stem in imp.module or target_stem in imp.imported_names):
                    matches.append(imp)
            return matches
        return []

    def trace_calls(self, entry_symbol: str, max_depth: int = 3) -> dict[str, Any]:
        """Build static call chain starting from entry_symbol."""
        visited: set[str] = set()

        def _trace(current_name: str, depth: int) -> dict[str, Any]:
            if depth >= max_depth or current_name in visited:
                return {"name": current_name, "calls": []}

            visited.add(current_name)
            callees = [c.callee_name for c in self.calls if c.caller_name == current_name]

            children = []
            for callee in callees:
                children.append(_trace(callee, depth + 1))

            visited.remove(current_name)
            return {"name": current_name, "calls": children}

        return _trace(entry_symbol, 0)
