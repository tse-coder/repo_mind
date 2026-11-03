"""
Unit tests for the 4 reverse-engineering tools and the Mermaid sanitizer.
"""

from pathlib import Path
from backend.tools.extract_api_contracts import extract_api_contracts
from backend.tools.extract_data_models import extract_data_models
from backend.tools.trace_data_flow import trace_data_flow
from backend.tools.map_architecture_layers import map_architecture_layers
from backend.knowledge.mermaid_sanitizer import sanitize_mermaid_code, is_valid_mermaid

SAMPLE_REPO = str(Path(__file__).resolve().parent.parent / "fixtures" / "sample_repo")


def test_extract_api_contracts():
    res = extract_api_contracts(SAMPLE_REPO)
    assert res["status"] == "SUCCESS"
    assert res["endpoint_count"] >= 1
    paths = [e["path"] for e in res["endpoints"]]
    assert any("/api/login" in p for p in paths)


def test_extract_data_models():
    res = extract_data_models(SAMPLE_REPO)
    assert res["status"] == "SUCCESS"
    assert res["model_count"] >= 1
    names = [m["model_name"] for m in res["models"]]
    assert "User" in names
    user_model = next(m for m in res["models"] if m["model_name"] == "User")
    field_names = [f["name"] for f in user_model["fields"]]
    assert "id" in field_names
    assert "email" in field_names


def test_trace_data_flow():
    res = trace_data_flow(SAMPLE_REPO, entry_symbol="login_handler")
    assert res["status"] == "SUCCESS"
    assert res["hop_count"] >= 2
    callees = [step["callee"] for step in res["flow_steps"]]
    assert "login_handler" in callees
    assert "authenticate" in callees


def test_map_architecture_layers():
    res = map_architecture_layers(SAMPLE_REPO)
    assert res["status"] == "SUCCESS"
    assert res["layer_count"] >= 2
    layer_names = [l["name"] for l in res["layers"]]
    assert "Presentation" in layer_names
    assert "Domain" in layer_names


def test_mermaid_sanitizer():
    # Test adding missing flowchart header
    raw_missing_header = "A --> B"
    sanitized = sanitize_mermaid_code(raw_missing_header)
    assert "flowchart TD" in sanitized
    assert is_valid_mermaid(sanitized)

    # Test auto-quoting labels with parentheses inside brackets
    raw_unquoted = "flowchart TD\nRouter[api/auth.py:6 (login_handler)] --> Service[auth_service.py]"
    clean = sanitize_mermaid_code(raw_unquoted)
    assert 'Router["api/auth.py:6 (login_handler)"]' in clean
    assert is_valid_mermaid(clean)
