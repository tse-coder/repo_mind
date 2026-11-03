"""
extract_data_models tool for RepoMind.

Extracts data models, schemas, fields, and relationships across Pydantic,
SQLAlchemy, Django ORM, and Prisma schema definitions.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

from backend.knowledge.snapshot import resolve_repo_path


def _extract_python_models(file_path: Path, repo_root: Path) -> list[dict[str, Any]]:
    """Extract Pydantic and SQLAlchemy models from Python AST."""
    models: list[dict[str, Any]] = []
    try:
        source = file_path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(file_path))
    except Exception:
        return models

    rel_path = str(file_path.relative_to(repo_root))

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        base_names = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_names.append(base.id)
            elif isinstance(base, ast.Attribute):
                base_names.append(base.attr)

        # Check if likely a model or schema
        is_model = any(
            b in ("BaseModel", "Base", "Model", "DeclarativeBase", "Schema")
            for b in base_names
        ) or any(d.id == "dataclass" for d in node.decorator_list if isinstance(d, ast.Name))

        if not is_model:
            continue

        fields: list[dict[str, Any]] = []
        relationships: list[dict[str, Any]] = []

        for item in node.body:
            # Type-annotated assignment: name: str = ... or Column(...)
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                field_name = item.target.id
                field_type = "Any"
                if isinstance(item.annotation, ast.Name):
                    field_type = item.annotation.id
                elif isinstance(item.annotation, ast.Subscript) and isinstance(item.annotation.value, ast.Name):
                    field_type = item.annotation.value.id

                is_pk = field_name.lower() in ("id", "pk")
                fk_target = None

                # Inspect value for Column or ForeignKey or relationship
                if item.value and isinstance(item.value, ast.Call):
                    func_name = ""
                    if isinstance(item.value.func, ast.Name):
                        func_name = item.value.func.id
                    elif isinstance(item.value.func, ast.Attribute):
                        func_name = item.value.func.attr

                    if func_name == "relationship":
                        # Relationship call: relationship("Order", ...)
                        if item.value.args and isinstance(item.value.args[0], ast.Constant):
                            target_name = str(item.value.args[0].value)
                            relationships.append({
                                "target": target_name,
                                "type": "ONE_TO_MANY" if "list" in str(field_type).lower() else "MANY_TO_ONE",
                            })
                            continue

                    for arg in item.value.args:
                        if isinstance(arg, ast.Call) and getattr(arg.func, "id", "") == "ForeignKey":
                            if arg.args and isinstance(arg.args[0], ast.Constant):
                                fk_target = str(arg.args[0].value)

                fields.append({
                    "name": field_name,
                    "type": field_type,
                    "is_primary_key": is_pk,
                    "foreign_key": fk_target,
                })

        models.append({
            "model_name": node.name,
            "file_path": rel_path,
            "line_number": node.lineno,
            "bases": base_names,
            "fields": fields,
            "relationships": relationships,
        })

    return models


def _extract_prisma_models(file_path: Path, repo_root: Path) -> list[dict[str, Any]]:
    """Extract models from schema.prisma."""
    models: list[dict[str, Any]] = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return models

    rel_path = str(file_path.relative_to(repo_root))
    model_blocks = re.findall(r"model\s+(\w+)\s*\{([^}]+)\}", content)

    for name, body in model_blocks:
        fields = []
        relationships = []
        for line in body.splitlines():
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                f_name, f_type = parts[0], parts[1]
                is_pk = "@id" in line
                fk = None
                if "@relation" in line:
                    rel_match = re.search(r"references:\s*\[(\w+)\]", line)
                    if rel_match:
                        fk = rel_match.group(1)
                    relationships.append({"target": f_type.replace("[]", ""), "type": "RELATION"})
                fields.append({
                    "name": f_name,
                    "type": f_type,
                    "is_primary_key": is_pk,
                    "foreign_key": fk,
                })

        models.append({
            "model_name": name,
            "file_path": rel_path,
            "line_number": 1,
            "bases": ["PrismaModel"],
            "fields": fields,
            "relationships": relationships,
        })

    return models


def extract_data_models(
    repo_path: str,
    model_type_hint: str | None = None,
) -> dict[str, Any]:
    """
    Extract data models, schema definitions, and entity relationships.
    """
    root = resolve_repo_path(repo_path)
    if not root or not root.exists() or not root.is_dir():
        return {
            "status": "ERROR",
            "error": f"Repository path not found: {repo_path}",
        }

    all_models: list[dict[str, Any]] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part.startswith(".") or part in ("node_modules", "venv", ".venv", "__pycache__", "dist", "build") for part in path.parts):
            continue

        if path.suffix == ".py":
            models = _extract_python_models(path, root)
            all_models.extend(models)
        elif path.name == "schema.prisma":
            models = _extract_prisma_models(path, root)
            all_models.extend(models)

    return {
        "status": "SUCCESS",
        "model_count": len(all_models),
        "models": all_models,
    }
