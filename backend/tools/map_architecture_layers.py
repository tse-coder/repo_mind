"""
map_architecture_layers tool for RepoMind.

Analyzes package layouts, directory groupings, and inter-module dependencies
to partition the codebase into architectural layers (Presentation, Domain,
Persistence, Infrastructure) and calculate inter-layer connections.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.knowledge.ast_parser import RepoASTIndex
from backend.knowledge.snapshot import resolve_repo_path


LAYER_KEYWORDS = {
    "Presentation": ("api", "router", "route", "controller", "endpoint", "handler", "view", "pages", "app"),
    "Domain": ("service", "core", "domain", "logic", "usecase", "manager", "policy"),
    "Persistence": ("db", "model", "repository", "repo", "schema", "entity", "database", "store"),
    "Infrastructure": ("config", "util", "helper", "common", "client", "middleware", "auth", "gateway"),
}


def _classify_layer(rel_path: str) -> str:
    """Classify a relative file path into an architectural layer."""
    lower_path = rel_path.lower().replace("\\", "/")
    parts = lower_path.split("/")

    for layer, keywords in LAYER_KEYWORDS.items():
        for kw in keywords:
            if any(part == kw or part.startswith(kw) or part.endswith(kw) for part in parts):
                return layer

    return "Domain"  # Default central layer


def map_architecture_layers(
    repo_path: str,
    max_depth: int = 3,
) -> dict[str, Any]:
    """
    Map codebase structure into architectural tiers and inter-tier dependencies.
    """
    root = resolve_repo_path(repo_path)
    if not root or not root.exists() or not root.is_dir():
        return {
            "status": "ERROR",
            "error": f"Repository path not found: {repo_path}",
        }

    ast_index = RepoASTIndex(str(root))

    layers: dict[str, list[dict[str, Any]]] = {
        "Presentation": [],
        "Domain": [],
        "Persistence": [],
        "Infrastructure": [],
    }

    # Group files and symbols by layer
    file_to_layer: dict[str, str] = {}
    for s in ast_index.symbols:
        if s.file_path not in file_to_layer:
            layer_name = _classify_layer(s.file_path)
            file_to_layer[s.file_path] = layer_name

    # Collect unique components per layer
    for file_path, layer_name in file_to_layer.items():
        symbols = [s.name for s in ast_index.symbols if s.file_path == file_path and s.kind in ("class", "function")]
        layers[layer_name].append({
            "file_path": file_path,
            "symbols": symbols[:5],
        })

    # Calculate dependencies between layers based on import graph
    inter_layer_edges: set[tuple[str, str]] = set()
    for imp in ast_index.imports:
        src_file = imp.source_file
        src_layer = file_to_layer.get(src_file)

        # Check if imported module matches another file in the repo
        target_file = None
        for known_file in file_to_layer:
            known_stem = Path(known_file).stem
            if imp.module.endswith(known_stem) or any(name == known_stem for name in imp.imported_names):
                target_file = known_file
                break

        if target_file and src_layer:
            target_layer = file_to_layer.get(target_file)
            if target_layer and src_layer != target_layer:
                inter_layer_edges.add((src_layer, target_layer))

    # Format layers and edges for diagram generation
    formatted_layers = [
        {
            "name": layer,
            "component_count": len(components),
            "components": components[:8],  # bound to prevent diagram clutter
        }
        for layer, components in layers.items()
        if components
    ]

    formatted_edges = [
        {"from_layer": edge[0], "to_layer": edge[1]}
        for edge in sorted(inter_layer_edges)
    ]

    return {
        "status": "SUCCESS",
        "layer_count": len(formatted_layers),
        "layers": formatted_layers,
        "inter_layer_dependencies": formatted_edges,
    }
