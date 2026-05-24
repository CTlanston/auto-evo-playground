"""Dispatch workers based on a plan.md.

A plan looks like:

    1. [code] Implement reverse_string in src/utils.py.
    2. [rw]   Document reverse_string in README.md.
    3. [code] Add tests/test_reverse_string.py.

This module:
  - Parses such lines into (kind, name, subtask) tuples.
  - Issues `gh workflow run worker.yml` for each, passing inputs.
  - code subtasks share a concurrency group (serial); rw subtasks each get a
    unique name (parallel-eligible). Concurrency is enforced by worker.yml,
    not by this dispatcher — we just fire-and-forget the workflow_dispatch.
"""
from __future__ import annotations

import logging
import re
import subprocess
from dataclasses import dataclass
from typing import List

LOG = logging.getLogger("orchestrator.dispatch")

# Matches: "1. [code] ..." or "- [rw] ..." etc.
# Case-insensitive on the kind tag.
SUBTASK_RE = re.compile(
    r"^\s*(?:\d+\.|[-*])\s*\[\s*(?P<kind>code|rw)\s*\]\s*(?P<text>.+?)\s*$",
    re.IGNORECASE,
)


@dataclass
class Subtask:
    kind: str   # "code" or "rw"
    name: str   # unique within an issue, e.g. "code-1", "rw-2"
    text: str   # the prose description (right-hand side of the bullet)


def parse_plan(plan_md: str) -> List[Subtask]:
    """Extract [code]/[rw] subtasks from a plan.md document.

    Lines without a [code] / [rw] tag (titles, prose paragraphs, blockquotes)
    are ignored — they don't dispatch workers.
    """
    subtasks: List[Subtask] = []
    code_idx = 0
    rw_idx = 0
    for line in plan_md.splitlines():
        m = SUBTASK_RE.match(line)
        if not m:
            continue
        kind = m.group("kind").lower()
        text = m.group("text").strip()
        if kind == "code":
            code_idx += 1
            name = f"code-{code_idx}"
        else:
            rw_idx += 1
            name = f"rw-{rw_idx}"
        subtasks.append(Subtask(kind=kind, name=name, text=text))
    return subtasks


def dispatch_one(*, repo: str, branch: str, issue_number: int,
                 subtask: Subtask, dry_run: bool = False) -> None:
    """Issue `gh workflow run worker.yml` for a single subtask."""
    cmd = [
        "gh", "workflow", "run", "worker.yml",
        "--repo", repo,
        "--ref", branch,
        "-f", f"issue={issue_number}",
        "-f", f"kind={subtask.kind}",
        "-f", f"name={subtask.name}",
        "-f", f"subtask={subtask.text}",
        "-f", f"branch={branch}",
    ]
    LOG.info("dispatch: kind=%s name=%s text=%r", subtask.kind, subtask.name, subtask.text)
    if dry_run:
        LOG.info("  (dry-run) would invoke: %s", " ".join(cmd))
        return
    subprocess.run(cmd, check=True)


def dispatch_all(*, repo: str, branch: str, issue_number: int,
                 plan_md: str, dry_run: bool = False) -> List[Subtask]:
    """Parse the plan and fire one workflow_dispatch per subtask.

    Returns the list of subtasks dispatched (mainly so callers can announce
    them on the issue thread).
    """
    subtasks = parse_plan(plan_md)
    if not subtasks:
        LOG.warning("plan.md contained no [code]/[rw] subtasks — nothing to dispatch")
        return []
    for st in subtasks:
        dispatch_one(repo=repo, branch=branch, issue_number=issue_number,
                     subtask=st, dry_run=dry_run)
    return subtasks


# ---------------------------------------------------------------------------
# Worker completion check — used by tick() to decide when to open the PR.
# ---------------------------------------------------------------------------

def workers_all_done(branch: str, subtasks: List[Subtask]) -> bool:
    """True iff every subtask has a corresponding workers/<name>/done.md on `branch`.

    Uses `git ls-tree` against the remote ref so this is callable from any
    checkout state. The branch must already be fetched (orchestrator/tick.py
    fetches it before calling this).
    """
    if not subtasks:
        return False
    for st in subtasks:
        path = f"workers/{st.name}/done.md"
        proc = subprocess.run(
            ["git", "ls-tree", "-r", f"origin/{branch}", "--name-only", path],
            check=False, capture_output=True, text=True,
        )
        if proc.returncode != 0 or path not in proc.stdout:
            LOG.info("worker %s not done yet (missing %s)", st.name, path)
            return False
    return True
