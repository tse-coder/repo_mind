"""
extract_api_contracts tool for RepoMind.

Scans the target repository to extract API endpoints, HTTP methods, route paths,
request/response schemas, and handler symbols across Python and TypeScript frameworks.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

from backend.knowledge.snapshot import resolve_repo_path


HTTP_METHODS = {"get", "post", "put", "delete", "patch", "options", "head"}


def _extract_python_routes(file_path: Path, repo_root: Path) -> list[dict[str, Any]]:
    """Extract FastAPI, Flask, and Django routes from a Python file using AST."""
    endpoints: list[dict[str, Any]] = []
    try:
        source = file_path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(file_path))
    except Exception:
        return endpoints

    rel_path = str(file_path.relative_to(repo_root))

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        for decorator in node.decorator_list:
            # Matches @app.get("/path") or @router.post("/path")
            if isinstance(decorator, ast.Call):
                func = decorator.func
                method: str | None = None
                path: str = ""

                # Attribute call: e.g. @router.get(...)
                if isinstance(func, ast.Attribute) and func.attr.lower() in HTTP_METHODS:
                    method = func.attr.upper()
                # Attribute call: e.g. @app.route("/path", methods=["GET"])
                elif isinstance(func, ast.Attribute) and func.attr.lower() == "route":
                    method = "GET"
                    for kw in decorator.keywords:
                        if kw.arg == "methods" and isinstance(kw.value, (ast.List, ast.Tuple)):
                            methods_found = [
                                elt.value for elt in kw.value.elts if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                            ]
                            if methods_found:
                                method = "/".join(methods_found).upper()

                if method:
                    if decorator.args and isinstance(decorator.args[0], ast.Constant):
                        path = str(decorator.args[0].value)

                    # Inspect arguments for request schema
                    req_schema = None
                    for arg in node.args.args:
                        if arg.arg not in ("self", "cls", "request", "db", "session"):
                            if arg.annotation and isinstance(arg.annotation, ast.Name):
                                req_schema = arg.annotation.id
                                break

                    # Inspect return annotation for response schema
                    resp_schema = None
                    if node.returns and isinstance(node.returns, ast.Name):
                        resp_schema = node.returns.id

                    endpoints.append({
                        "method": method,
                        "path": path or "/",
                        "handler": node.name,
                        "file_path": rel_path,
                        "line_number": node.lineno,
                        "request_schema": req_schema,
                        "response_schema": resp_schema,
                    })

        # Fallback: check docstrings for route specifications (e.g. "HTTP POST handler for /api/login")
        docstring = ast.get_docstring(node)
        if docstring and not any(e["handler"] == node.name for e in endpoints):
            match = re.search(r"(?:HTTP\s+)?(GET|POST|PUT|DELETE|PATCH)\s+(?:handler\s+(?:for\s+)?|endpoint\s+(?:for\s+)?|route\s+(?:for\s+)?)?(/[\w\-/{}]+)", docstring, re.IGNORECASE)
            if match:
                req_schema = None
                for arg in node.args.args:
                    if arg.arg not in ("self", "cls", "request"):
                        if arg.annotation and isinstance(arg.annotation, ast.Name):
                            req_schema = arg.annotation.id
                            break
                resp_schema = node.returns.id if node.returns and isinstance(node.returns, ast.Name) else None

                endpoints.append({
                    "method": match.group(1).upper(),
                    "path": match.group(2),
                    "handler": node.name,
                    "file_path": rel_path,
                    "line_number": node.lineno,
                    "request_schema": req_schema,
                    "response_schema": resp_schema,
                })

    return endpoints


def _extract_ts_js_routes(file_path: Path, repo_root: Path) -> list[dict[str, Any]]:
    """Extract Express and Next.js App Router routes using regex."""
    endpoints: list[dict[str, Any]] = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return endpoints

    rel_path = str(file_path.relative_to(repo_root))

    # Next.js App Router: app/api/.../route.ts
    if "api" in rel_path and ("route.ts" in rel_path or "route.js" in rel_path):
        # Extract methods exported: export async function GET / POST ...
        route_path = "/" + str(file_path.parent.relative_to(repo_root)).replace("\\", "/")
        matches = re.finditer(
            r"export\s+(?:async\s+)?function\s+(GET|POST|PUT|DELETE|PATCH)\s*\(",
            content,
        )
        for m in matches:
            endpoints.append({
                "method": m.group(1),
                "path": route_path,
                "handler": m.group(1).lower(),
                "file_path": rel_path,
                "line_number": content[:m.start()].count("\n") + 1,
                "request_schema": "Request",
                "response_schema": "Response",
            })

    # Express: router.get('/path', ...), app.post('/path', ...)
    express_matches = re.finditer(
        r"(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*['\"`]([^'\"`]+)['\"`]",
        content,
        re.IGNORECASE,
    )
    for m in express_matches:
        endpoints.append({
            "method": m.group(1).upper(),
            "path": m.group(2),
            "handler": "anonymous",
            "file_path": rel_path,
            "line_number": content[:m.start()].count("\n") + 1,
            "request_schema": None,
            "response_schema": None,
        })

    return endpoints


def extract_api_contracts(
    repo_path: str,
    framework_hint: str | None = None,
) -> dict[str, Any]:
    """
    Scan repository to discover and catalogue API routes and contracts.
    """
    root = resolve_repo_path(repo_path)
    if not root or not root.exists() or not root.is_dir():
        return {
            "status": "ERROR",
            "error": f"Repository path not found: {repo_path}",
        }

    all_endpoints: list[dict[str, Any]] = []
    frameworks_detected = set()

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        # Skip node_modules, .git, venv, caches
        if any(part.startswith(".") or part in ("node_modules", "venv", ".venv", "__pycache__", "dist", "build") for part in path.parts):
            continue

        if path.suffix == ".py":
            routes = _extract_python_routes(path, root)
            if routes:
                frameworks_detected.add("Python (FastAPI/Flask)")
                all_endpoints.extend(routes)
        elif path.suffix in (".ts", ".js", ".tsx", ".jsx"):
            routes = _extract_ts_js_routes(path, root)
            if routes:
                frameworks_detected.add("Node.js/TypeScript (Express/Next.js)")
                all_endpoints.extend(routes)

    # Sort endpoints by path and method
    all_endpoints.sort(key=lambda e: (e["path"], e["method"]))

    return {
        "status": "SUCCESS",
        "frameworks_detected": list(frameworks_detected),
        "endpoint_count": len(all_endpoints),
        "endpoints": all_endpoints,
    }
