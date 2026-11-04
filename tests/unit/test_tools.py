"""
Unit tests for all 10 execution tools, snapshot resolver, and secret scanner.
"""

from pathlib import Path

from backend.knowledge.docs_index import chunk_markdown_by_headings, discover_doc_files
from backend.knowledge.secret_scanner import redact_secrets, scan_for_secrets
from backend.knowledge.snapshot import get_snapshot_info
from backend.tools import dispatch_tool
from backend.tools.explore_tree import explore_tree
from backend.tools.find_references import find_references
from backend.tools.get_relationships import get_relationships
from backend.tools.get_symbol import get_symbol
from backend.tools.read_file import read_file
from backend.tools.search_code import search_code
from backend.tools.search_docs import search_docs
from backend.tools.search_symbols import search_symbols
from backend.tools.semantic_search import semantic_search
from backend.tools.trace_calls import trace_calls

SAMPLE_REPO = Path(__file__).resolve().parent.parent / "fixtures" / "sample_repo"


def test_snapshot_resolver():
    snap = get_snapshot_info(SAMPLE_REPO)
    assert snap.snapshot_id is not None
    assert len(snap.snapshot_id) > 0


def test_secret_scanner():
    config_file = SAMPLE_REPO / "config.py"
    content = config_file.read_text()
    secrets = scan_for_secrets(content)
    assert len(secrets) >= 1
    assert any(s.pattern_name == "AWS_ACCESS_KEY" for s in secrets)

    redacted = redact_secrets(content)
    assert "AKIAIOSFODNN7EXAMPLE" not in redacted
    assert "[REDACTED_AWS_ACCESS_KEY]" in redacted


def test_explore_tree():
    res = explore_tree(str(SAMPLE_REPO), subpath=".", depth=2)
    assert res["status"] == "SUCCESS"
    assert res["entry_count"] > 0
    paths = [e["path"] for e in res["entries"]]
    assert any("README.md" in p for p in paths)
    assert any("services" in p for p in paths)


def test_read_file():
    res = read_file(str(SAMPLE_REPO), file_path="README.md", start_line=1, end_line=5)
    assert res["status"] == "SUCCESS"
    assert res["start_line"] == 1
    assert res["end_line"] == 5
    assert "Sample Project" in res["content"]
    assert len(res["content_hash"]) == 16


def test_search_code_literal():
    res = search_code(str(SAMPLE_REPO), query="register_user", is_regex=False)
    assert res["status"] == "SUCCESS"
    assert res["match_count"] >= 1
    assert any("auth_service.py" in m["file_path"] for m in res["matches"])


def test_search_code_regex():
    res = search_code(str(SAMPLE_REPO), query=r"def \w+_handler", is_regex=True)
    assert res["status"] == "SUCCESS"
    assert res["match_count"] >= 2


def test_search_symbols():
    res = search_symbols(str(SAMPLE_REPO), query="AuthService")
    assert res["status"] == "SUCCESS"
    assert res["match_count"] == 1
    sym = res["symbols"][0]
    assert sym["name"] == "AuthService"
    assert sym["kind"] == "class"


def test_get_symbol():
    res = get_symbol(str(SAMPLE_REPO), symbol_name="register_user")
    assert res["status"] == "SUCCESS"
    sym = res["symbol"]
    assert sym["name"] == "register_user"
    assert "def register_user" in sym["definition_source"]


def test_find_references():
    res = find_references(str(SAMPLE_REPO), symbol_name="authenticate")
    assert res["status"] == "SUCCESS"
    assert res["reference_count"] >= 1
    assert any("auth_router.py" in r["file_path"] for r in res["references"])


def test_get_relationships():
    res = get_relationships(str(SAMPLE_REPO), file_path="services/auth_service.py", direction="imports")
    assert res["status"] == "SUCCESS"
    modules = [r["module"] for r in res["relationships"]]
    assert any("models.user" in m for m in modules)


def test_trace_calls():
    res = trace_calls(str(SAMPLE_REPO), entry_symbol="login_handler", depth=3)
    assert res["status"] == "SUCCESS"
    tree = res["call_tree"]
    assert tree["name"] == "login_handler"
    callee_names = [c["name"] for c in tree["calls"]]
    assert "authenticate" in callee_names


def test_semantic_search(tmp_path):
    res = semantic_search(str(SAMPLE_REPO), query="user authentication and tokens", k=3)
    assert res["status"] == "SUCCESS"
    assert res["result_count"] >= 1
    assert any("auth" in r["file_path"].lower() for r in res["results"])


def test_discover_doc_files():
    files = discover_doc_files(SAMPLE_REPO)
    rels = {str(p.relative_to(SAMPLE_REPO)) for p in files}
    assert "README.md" in rels
    assert "docs/adr/0001-session-storage.md" in rels
    assert "docs/retry-policy.md" in rels
    assert not any(p.suffix == ".py" for p in files)


def test_chunk_markdown_by_headings():
    adr = SAMPLE_REPO / "docs" / "adr" / "0001-session-storage.md"
    chunks = chunk_markdown_by_headings(adr, SAMPLE_REPO)
    assert len(chunks) >= 2
    headings = {c.heading for c in chunks}
    assert any("Redis for Session Storage" in h for h in headings)
    assert any("Decision" in h for h in headings)
    assert any("Redis over Memcached" in c.content for c in chunks)


def test_search_docs():
    res = search_docs(
        str(SAMPLE_REPO),
        query="Why did we choose Redis over Memcached for session storage?",
        k=3,
    )
    assert res["status"] == "SUCCESS"
    assert res["result_count"] >= 1
    joined = " ".join(r["snippet"].lower() + r["file_path"].lower() for r in res["results"])
    assert "redis" in joined
    assert any("adr" in r["file_path"].lower() or "docs" in r["file_path"].lower() for r in res["results"])


def test_dispatch_tool():
    res = dispatch_tool(
        repo_path=str(SAMPLE_REPO),
        tool_slug="read_file",
        arguments={"file_path": "README.md", "start_line": 1, "end_line": 3},
    )
    assert res["status"] == "SUCCESS"
    assert "Sample Project" in res["content"]
