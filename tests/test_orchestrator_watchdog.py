"""Tests for orchestrator.watchdog — branch-name parsing + stale detection thresholds."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from orchestrator.watchdog import SHADOW_BRANCH_RE, stale_shadow_branches


def test_shadow_branch_regex_matches_canonical_form():
    assert SHADOW_BRANCH_RE.match("shadow/issue-42").group(1) == "42"
    assert SHADOW_BRANCH_RE.match("shadow/issue-1234").group(1) == "1234"


def test_shadow_branch_regex_rejects_non_issue_branches():
    assert SHADOW_BRANCH_RE.match("shadow/foo") is None
    assert SHADOW_BRANCH_RE.match("main") is None
    assert SHADOW_BRANCH_RE.match("shadow/issue-abc") is None
    assert SHADOW_BRANCH_RE.match("shadow/issue-42-extra") is None


def _ts(hours_ago: int) -> str:
    dt = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    # Trim microseconds; ISO-strict format git uses.
    return dt.replace(microsecond=0).isoformat()


def test_stale_shadow_branches_flags_older_than_threshold():
    fake_output = (
        f"origin/shadow/issue-1 {_ts(48)}\n"
        f"origin/shadow/issue-2 {_ts(1)}\n"
        f"origin/shadow/issue-3 {_ts(100)}\n"
        f"origin/main {_ts(48)}\n"          # not a shadow/issue branch — ignored
    )
    with patch("orchestrator.watchdog._run") as run_mock:
        run_mock.return_value.returncode = 0
        run_mock.return_value.stdout = fake_output
        run_mock.return_value.stderr = ""
        stale = stale_shadow_branches(stuck_hours=24)
    assert sorted(stale) == [(1, "shadow/issue-1"), (3, "shadow/issue-3")]


def test_stale_shadow_branches_empty_when_all_recent():
    fake_output = (
        f"origin/shadow/issue-1 {_ts(1)}\n"
        f"origin/shadow/issue-2 {_ts(2)}\n"
    )
    with patch("orchestrator.watchdog._run") as run_mock:
        run_mock.return_value.returncode = 0
        run_mock.return_value.stdout = fake_output
        run_mock.return_value.stderr = ""
        stale = stale_shadow_branches(stuck_hours=24)
    assert stale == []


def test_stale_shadow_branches_handles_unparseable_date_lines():
    fake_output = (
        f"origin/shadow/issue-1 not-a-date\n"
        f"origin/shadow/issue-2 {_ts(100)}\n"
    )
    with patch("orchestrator.watchdog._run") as run_mock:
        run_mock.return_value.returncode = 0
        run_mock.return_value.stdout = fake_output
        run_mock.return_value.stderr = ""
        stale = stale_shadow_branches(stuck_hours=24)
    # Bad line skipped; good stale line surfaces.
    assert stale == [(2, "shadow/issue-2")]


def test_stale_shadow_branches_returns_empty_when_git_fails():
    with patch("orchestrator.watchdog._run") as run_mock:
        run_mock.return_value.returncode = 1
        run_mock.return_value.stdout = ""
        run_mock.return_value.stderr = "fatal: not a git repository"
        assert stale_shadow_branches(stuck_hours=24) == []
