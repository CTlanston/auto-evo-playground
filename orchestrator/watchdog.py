"""Watchdog — flag stuck issues and stale shadow branches.

Invoked hourly by .github/workflows/watchdog.yml. For each suspect issue:
  - posts a comment explaining what's stuck
  - adds the `agent:blocked` label so the orchestrator skips it
"""
from __future__ import annotations

import argparse
import logging
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from orchestrator.daily_digest import in_progress_issues, is_stuck

LOG = logging.getLogger("orchestrator.watchdog")

LABEL_BLOCKED = "agent:blocked"
LABEL_IN_PROGRESS = "agent:in-progress"
SHADOW_BRANCH_RE = re.compile(r"^shadow/issue-(\d+)$")


def _run(cmd: List[str], *, check: bool = True) -> subprocess.CompletedProcess:
    LOG.debug("$ %s", " ".join(cmd))
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

def stale_shadow_branches(*, stuck_hours: int) -> List[Tuple[int, str]]:
    """Find shadow/issue-<n> remote branches whose tip is older than `stuck_hours`.

    Returns a list of (issue_number, branch_name).
    """
    proc = _run([
        "git", "for-each-ref",
        "--format=%(refname:short) %(committerdate:iso-strict)",
        "refs/remotes/origin/shadow",
    ], check=False)
    if proc.returncode != 0:
        LOG.warning("git for-each-ref failed: %s", proc.stderr.strip())
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=stuck_hours)
    stale: List[Tuple[int, str]] = []
    for line in proc.stdout.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) != 2:
            continue
        refname, iso = parts
        # refname is `origin/shadow/issue-<n>` — strip the remote prefix.
        branch = refname.split("/", 1)[1] if refname.startswith("origin/") else refname
        m = SHADOW_BRANCH_RE.match(branch)
        if not m:
            continue
        try:
            committer_dt = datetime.fromisoformat(iso)
            if committer_dt.tzinfo is None:
                committer_dt = committer_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if committer_dt < cutoff:
            stale.append((int(m.group(1)), branch))
    return stale


def stuck_in_progress(repo: str, *, stuck_hours: int) -> List[dict]:
    issues = in_progress_issues(repo)
    return [i for i in issues if is_stuck(i["updatedAt"], stuck_hours)]


# ---------------------------------------------------------------------------
# Action
# ---------------------------------------------------------------------------

def mark_blocked(repo: str, issue_number: int, reason: str) -> None:
    body = (
        f"🐶 **Watchdog alert** — labelling `{LABEL_BLOCKED}`.\n\n"
        f"Reason: {reason}\n\n"
        f"The orchestrator will skip this issue on subsequent ticks until a "
        f"human removes `{LABEL_BLOCKED}` and (if needed) clears `agent:in-progress`."
    )
    _run([
        "gh", "issue", "comment", str(issue_number),
        "--repo", repo,
        "--body", body,
    ], check=False)
    _run([
        "gh", "issue", "edit", str(issue_number),
        "--repo", repo,
        "--add-label", LABEL_BLOCKED,
    ], check=False)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(repo: str, stuck_hours: int) -> int:
    flagged: set = set()

    for issue in stuck_in_progress(repo, stuck_hours=stuck_hours):
        n = issue["number"]
        if n in flagged:
            continue
        flagged.add(n)
        reason = (
            f"Issue carries `{LABEL_IN_PROGRESS}` but has had no update for "
            f"more than {stuck_hours}h (last update: {issue['updatedAt']})."
        )
        LOG.info("flagging stuck issue #%d", n)
        mark_blocked(repo, n, reason)

    for issue_number, branch in stale_shadow_branches(stuck_hours=stuck_hours):
        if issue_number in flagged:
            continue
        flagged.add(issue_number)
        reason = (
            f"Shadow branch `{branch}` has not received any commits for "
            f"more than {stuck_hours}h."
        )
        LOG.info("flagging stale branch %s (issue #%d)", branch, issue_number)
        mark_blocked(repo, issue_number, reason)

    LOG.info("watchdog finished — flagged %d issues", len(flagged))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Watchdog tick")
    p.add_argument("--repo", required=True)
    p.add_argument("--stuck-hours", type=int, default=6)
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    return run(args.repo, args.stuck_hours)


if __name__ == "__main__":
    sys.exit(main())
