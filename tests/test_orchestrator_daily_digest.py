"""Tests for orchestrator.daily_digest pure functions (render + is_stuck + has_fail_check)."""
from datetime import datetime, timedelta, timezone

from orchestrator.daily_digest import (
    has_fail_check,
    is_stuck,
    render_digest,
)


def test_render_digest_with_all_sections():
    body = render_digest(
        merged=[{"number": 10, "title": "Closes #5: foo"}],
        open_with_fail=[{
            "number": 12, "title": "Closes #6: bar", "headRefName": "shadow/issue-6",
        }],
        queue=[
            {"number": 7, "title": "[agent] add reverse_string"},
            {"number": 8, "title": "[agent] add palindrome check"},
        ],
        stuck=[{"number": 4, "title": "[agent] stuck task", "updatedAt": "2026-05-21T00:00:00Z"}],
    )
    assert "### ✅ Merged in the last 24h" in body
    assert "#10 — Closes #5: foo" in body
    assert "#12 — Closes #6: bar" in body
    assert "shadow/issue-6" in body
    assert "Queue depth: 2" in body
    assert "#7 — [agent] add reverse_string" in body
    assert "Stuck in-progress" in body
    assert "#4 — [agent] stuck task" in body


def test_render_digest_empty_sections_show_none():
    body = render_digest(merged=[], open_with_fail=[], queue=[], stuck=[])
    # All four sections present with "(none)" or "0".
    assert body.count("_(none)_") == 3   # merged + open_with_fail + stuck
    assert "Queue depth: 0" in body


def test_render_digest_queue_truncates_at_ten():
    queue = [{"number": i, "title": f"task {i}"} for i in range(1, 16)]
    body = render_digest(merged=[], open_with_fail=[], queue=queue, stuck=[])
    assert "Queue depth: 15" in body
    assert "and 5 more" in body
    # Only first 10 are itemized.
    assert "task 10" in body
    assert "task 11" not in body


def test_is_stuck_true_when_older_than_threshold():
    long_ago = (datetime.now(timezone.utc) - timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert is_stuck(long_ago, hours=24) is True


def test_is_stuck_false_when_recent():
    recent = (datetime.now(timezone.utc) - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert is_stuck(recent, hours=24) is False


def test_is_stuck_false_on_bad_input():
    assert is_stuck("not a date", hours=24) is False


def test_has_fail_check_detects_failure():
    pr = {"statusCheckRollup": [
        {"conclusion": "success"},
        {"conclusion": "failure"},
    ]}
    assert has_fail_check(pr) is True


def test_has_fail_check_handles_commit_status_state_field():
    """gh's statusCheckRollup is heterogeneous — commit statuses use `state`, check runs use `conclusion`."""
    pr = {"statusCheckRollup": [
        {"state": "error"},
    ]}
    assert has_fail_check(pr) is True


def test_has_fail_check_all_green_returns_false():
    pr = {"statusCheckRollup": [
        {"conclusion": "success"},
        {"state": "success"},
    ]}
    assert has_fail_check(pr) is False


def test_has_fail_check_handles_empty_rollup():
    assert has_fail_check({"statusCheckRollup": []}) is False
    assert has_fail_check({}) is False
