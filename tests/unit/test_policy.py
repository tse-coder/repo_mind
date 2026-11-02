"""
Unit tests for the Policy Gateway, path sandboxing, and output framing.
"""

from pathlib import Path
import pytest

from backend.policy.gateway import PolicyGateway
from backend.policy.framing import frame_untrusted_content

SAMPLE_REPO = Path(__file__).resolve().parent.parent / "fixtures" / "sample_repo"


def test_policy_gateway_approved_tool():
    gateway = PolicyGateway(str(SAMPLE_REPO))
    res = gateway.validate(
        tool_slug="read_file",
        arguments={"file_path": "README.md", "start_line": 1},
        step_count=1,
        max_steps=25,
    )
    assert res.allowed is True
    assert res.status == "APPROVED"


def test_policy_gateway_denied_disallowed_tool():
    gateway = PolicyGateway(str(SAMPLE_REPO))
    res = gateway.validate(
        tool_slug="run_bash_script",
        arguments={"cmd": "ls"},
        step_count=1,
        max_steps=25,
    )
    assert res.allowed is False
    assert res.status == "DENIED"
    assert "not on the permitted tools allowlist" in res.reason


def test_policy_gateway_denied_budget_exceeded():
    gateway = PolicyGateway(str(SAMPLE_REPO))
    res = gateway.validate(
        tool_slug="read_file",
        arguments={"file_path": "README.md"},
        step_count=25,
        max_steps=25,
    )
    assert res.allowed is False
    assert res.status == "DENIED"
    assert "Step budget reached" in res.reason


def test_policy_gateway_denied_path_traversal():
    gateway = PolicyGateway(str(SAMPLE_REPO))
    res = gateway.validate(
        tool_slug="read_file",
        arguments={"file_path": "../../etc/passwd"},
        step_count=1,
        max_steps=25,
    )
    assert res.allowed is False
    assert res.status == "DENIED"
    assert "escapes the repository root" in res.reason


def test_frame_untrusted_content():
    raw_text = "def hello(): pass"
    framed = frame_untrusted_content(source_tool="read_file", raw_output=raw_text, file_path="main.py")
    assert "<<<UNTRUSTED_REPOSITORY_DATA" in framed
    assert 'source="read_file"' in framed
    assert 'file="main.py"' in framed
    assert "<<<END_UNTRUSTED_REPOSITORY_DATA>>>" in framed
    assert "def hello(): pass" in framed


def test_frame_untrusted_content_redacts_secrets():
    content_with_secret = "api_key = 'AKIAIOSFODNN7EXAMPLE'"
    framed = frame_untrusted_content(source_tool="read_file", raw_output=content_with_secret)
    assert "AKIAIOSFODNN7EXAMPLE" not in framed
    assert "[REDACTED_AWS_ACCESS_KEY]" in framed
