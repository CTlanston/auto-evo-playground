"""Tests for validator.validate — evidence formatting, mock verdict, JUnit parsing.

These tests deliberately exercise the source-free guarantees: format_evidence
must produce text that contains NO source-code content, only paths + counts +
behavioral artifacts.
"""
from pathlib import Path

from validator.validate import (
    Evidence,
    FileEntry,
    TestSummary,
    _mock_verdict,
    _parse_junit_dir,
    format_evidence,
    parse_conclusion,
)


def test_parse_conclusion_pass_and_fail():
    assert parse_conclusion("PASS\n---\nReasons:\n- ok") == "success"
    assert parse_conclusion("FAIL\n---\nReasons:\n- nope") == "failure"
    assert parse_conclusion("pass\n---\nReasons:\n- ok") == "success"  # case-insensitive
    assert parse_conclusion("garbage output") == "neutral"
    assert parse_conclusion("") == "neutral"


def test_format_evidence_includes_no_source_content():
    """The single most important invariant: format_evidence MUST NOT echo
    file content under any circumstance. It accepts only paths, sizes,
    contract text, done.md text, test summary counts, and failing names.
    """
    ev = Evidence(
        contract_md="Behavioral criteria: foo() returns 42.",
        done_reports={
            "code-1": "I wrote a function and verified foo() == 42.",
        },
        file_manifest=[
            FileEntry(path="src/foo.py", additions=5, deletions=0),
            FileEntry(path="tests/test_foo.py", additions=10, deletions=0),
        ],
        test_summaries={
            "test-results-fast": TestSummary(
                passed=3, failed=0, skipped=0, errors=0, failing_names=[]),
        },
    )
    text = format_evidence(ev)

    # Things that should appear:
    assert "Behavioral criteria: foo() returns 42." in text
    assert "I wrote a function and verified foo() == 42." in text
    assert "`src/foo.py` (+5/-0)" in text
    assert "`tests/test_foo.py` (+10/-0)" in text
    assert "passed: 3" in text

    # Things that must NEVER appear (we never have access to source content
    # here, but lock the behavior so a future refactor that "helpfully"
    # injects content gets caught by this assertion).
    assert "def foo" not in text
    assert "return 42" not in text
    assert "import" not in text


def test_format_evidence_includes_failing_test_names_not_traces():
    ev = Evidence(
        contract_md="contract",
        done_reports={},
        file_manifest=[],
        test_summaries={
            "test-results-fast": TestSummary(
                passed=2, failed=1, skipped=0, errors=0,
                failing_names=["tests.test_foo::test_foo_returns_42"]),
        },
    )
    text = format_evidence(ev)
    assert "tests.test_foo::test_foo_returns_42" in text
    # No traceback / source artifacts should be present even if name contains "::"
    assert "Traceback" not in text
    assert ".py:" not in text


def test_mock_verdict_pass_when_all_signals_green():
    """Mock evaluator passes only when contract present + at least one done.md + no failed tests."""
    ev = Evidence(
        contract_md="A behavioral expectation.",
        done_reports={"code-1": "did the thing"},
        file_manifest=[],
        test_summaries={
            "test-results-fast": TestSummary(passed=3, failed=0, errors=0, skipped=0),
        },
    )
    verdict = _mock_verdict(format_evidence(ev))
    assert verdict.startswith("PASS")
    assert "Reasons:" in verdict


def test_mock_verdict_fails_when_test_fails():
    ev = Evidence(
        contract_md="A behavioral expectation.",
        done_reports={"code-1": "did the thing"},
        file_manifest=[],
        test_summaries={
            "test-results-fast": TestSummary(passed=2, failed=1, errors=0, skipped=0,
                                             failing_names=["x::y"]),
        },
    )
    verdict = _mock_verdict(format_evidence(ev))
    assert verdict.startswith("FAIL")
    assert "Remediation:" in verdict


def test_mock_verdict_fails_when_no_done_reports():
    ev = Evidence(
        contract_md="A behavioral expectation.",
        done_reports={},   # no workers reported done
        file_manifest=[FileEntry(path="src/x.py", additions=1, deletions=0)],
        test_summaries={
            "test-results-fast": TestSummary(passed=1, failed=0, errors=0, skipped=0),
        },
    )
    verdict = _mock_verdict(format_evidence(ev))
    assert verdict.startswith("FAIL")


def test_parse_junit_dir_counts(tmp_path: Path):
    """A junit XML with one passing and one failing case must report
    failed=1, passed=1, and surface the failing name (no trace).
    """
    junit = tmp_path / "junit-fast.xml"
    junit.write_text("""<?xml version="1.0"?>
<testsuites>
  <testsuite name="ts" tests="2" failures="1" errors="0" skipped="0">
    <testcase classname="tests.test_x" name="test_passes"/>
    <testcase classname="tests.test_x" name="test_fails">
      <failure message="boom">Traceback (...) AssertionError</failure>
    </testcase>
  </testsuite>
</testsuites>
""", encoding="utf-8")
    summary = _parse_junit_dir(tmp_path)
    assert summary.passed == 1
    assert summary.failed == 1
    assert summary.failing_names == ["tests.test_x::test_fails"]


def test_parse_junit_dir_empty_returns_zero_summary(tmp_path: Path):
    summary = _parse_junit_dir(tmp_path)
    assert summary.passed == 0
    assert summary.failed == 0
    assert summary.failing_names == []
