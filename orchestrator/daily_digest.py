"""Build + post the daily digest. Invoked by .github/workflows/daily-digest.yml.

The digest is a comment on a long-lived issue (titled `DIGEST_TITLE` — see
the workflow). If the issue does not exist, the script opens it.
"""
from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from typing import List, Optional

LOG = logging.getLogger("orchestrator.daily_digest")

LABEL_QUEUE = "agent:queue"
LABEL_IN_PROGRESS = "agent:in-progress"
STUCK_AFTER_HOURS = 24


def _run(cmd: List[str], *, check: bool = True) -> subprocess.CompletedProcess:
    LOG.debug("$ %s", " ".join(cmd))
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def _gh_json(args: List[str]) -> list:
    proc = _run(args)
    return json.loads(proc.stdout or "[]")


def find_or_create_digest_issue(repo: str, title: str) -> int:
    """Find the digest issue by exact title; create if missing."""
    # gh issue list --search returns matches by title token; filter to exact.
    issues = _gh_json([
        "gh", "issue", "list",
        "--repo", repo,
        "--state", "all",
        "--search", f"in:title \"{title}\"",
        "--limit", "10",
        "--json", "number,title",
    ])
    for i in issues:
        if i["title"] == title:
            return i["number"]

    proc = _run([
        "gh", "issue", "create",
        "--repo", repo,
        "--title", title,
        "--body", "Long-lived issue: each day's digest is posted as a comment below.",
    ])
    # gh prints the URL; grab the number from the end.
    url = proc.stdout.strip().splitlines()[-1]
    num = int(url.rsplit("/", 1)[-1])
    return num


def merged_prs_recent(repo: str, hours: int = 24) -> list:
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%d")
    return _gh_json([
        "gh", "pr", "list",
        "--repo", repo,
        "--state", "merged",
        "--search", f"merged:>={since}",
        "--limit", "100",
        "--json", "number,title,mergedAt",
    ])


def open_prs(repo: str) -> list:
    return _gh_json([
        "gh", "pr", "list",
        "--repo", repo,
        "--state", "open",
        "--limit", "100",
        "--json", "number,title,headRefName,statusCheckRollup",
    ])


def queue_issues(repo: str) -> list:
    return _gh_json([
        "gh", "issue", "list",
        "--repo", repo,
        "--state", "open",
        "--label", LABEL_QUEUE,
        "--limit", "100",
        "--json", "number,title,createdAt",
    ])


def in_progress_issues(repo: str) -> list:
    return _gh_json([
        "gh", "issue", "list",
        "--repo", repo,
        "--state", "open",
        "--label", LABEL_IN_PROGRESS,
        "--limit", "100",
        "--json", "number,title,updatedAt",
    ])


def is_stuck(updated_at: str, hours: int) -> bool:
    """Return True if `updated_at` is older than `hours` ago."""
    try:
        # GitHub ISO format like 2026-05-23T19:30:00Z
        dt = datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return False
    return (datetime.now(timezone.utc) - dt) > timedelta(hours=hours)


def render_digest(*, merged: list, open_with_fail: list,
                  queue: list, stuck: list) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines: List[str] = [f"## 📋 Digest — {today}", ""]

    lines.append("### ✅ Merged in the last 24h")
    if merged:
        for pr in merged:
            lines.append(f"- #{pr['number']} — {pr['title']}")
    else:
        lines.append("- _(none)_")
    lines.append("")

    lines.append("### ❌ Open PRs needing attention (validator FAIL or red CI)")
    if open_with_fail:
        for pr in open_with_fail:
            lines.append(f"- #{pr['number']} — {pr['title']}  (branch: `{pr['headRefName']}`)")
    else:
        lines.append("- _(none)_")
    lines.append("")

    lines.append(f"### 📥 Queue depth: {len(queue)}")
    for issue in queue[:10]:
        lines.append(f"- #{issue['number']} — {issue['title']}")
    if len(queue) > 10:
        lines.append(f"- … and {len(queue) - 10} more")
    lines.append("")

    lines.append(f"### ⏳ Stuck in-progress (>{STUCK_AFTER_HOURS}h since last update)")
    if stuck:
        for issue in stuck:
            lines.append(f"- #{issue['number']} — {issue['title']} (updated {issue['updatedAt']})")
    else:
        lines.append("- _(none)_")

    return "\n".join(lines)


def has_fail_check(pr: dict) -> bool:
    rollup = pr.get("statusCheckRollup") or []
    for entry in rollup:
        # gh returns either a check_run or commit status; both have a "conclusion" or "state".
        concl = entry.get("conclusion") or entry.get("state") or ""
        if str(concl).lower() in {"failure", "failed", "error"}:
            return True
    return False


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Post the daily auto-evo digest")
    p.add_argument("--repo", required=True)
    p.add_argument("--digest-title", required=True)
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    merged = merged_prs_recent(args.repo, hours=24)
    open_all = open_prs(args.repo)
    open_with_fail = [pr for pr in open_all if has_fail_check(pr)]
    queue = queue_issues(args.repo)
    in_progress = in_progress_issues(args.repo)
    stuck = [i for i in in_progress if is_stuck(i["updatedAt"], STUCK_AFTER_HOURS)]

    body = render_digest(merged=merged, open_with_fail=open_with_fail,
                         queue=queue, stuck=stuck)
    print(body)

    issue_num = find_or_create_digest_issue(args.repo, args.digest_title)
    _run([
        "gh", "issue", "comment", str(issue_num),
        "--repo", args.repo,
        "--body", body,
    ])
    LOG.info("posted digest to issue #%d", issue_num)
    return 0


if __name__ == "__main__":
    sys.exit(main())
