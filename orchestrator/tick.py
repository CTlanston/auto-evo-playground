"""Orchestrator heartbeat — one tick of the self-evolving agent system.

Run by .github/workflows/orchestrator.yml on schedule (default: every 15 min)
and on workflow_dispatch.

Each tick:
  1. Check AGENT_FROZEN kill-switch — exit 0 if frozen.
  2. Pick the oldest open issue labelled `agent:queue` and NOT `agent:in-progress`.
     (If the queue is empty, exit 0 — Phase 8 will add self-evolution behavior.)
  3. Ensure a shadow branch `shadow/issue-<n>` exists, branching from main.
  4. Ask Claude (planning tools only — no Bash) to write `plan.md` + `contract.md`
     describing the work. Commit & push to the shadow branch.
  5. Label the issue `agent:in-progress`, comment with the plan.

This script is invoked from a GitHub Actions runner. Authentication:
  - GH_TOKEN env var (used by gh CLI) — must have repo write scope.
  - ANTHROPIC_API_KEY env var — for the Claude call (not needed in --dry-run).

Local development: pass --dry-run to skip both gh and Anthropic calls;
the script then operates on synthetic data so the control flow can be
exercised without secrets.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from typing import List, Optional

LOG = logging.getLogger("orchestrator.tick")

LABEL_QUEUE = "agent:queue"
LABEL_IN_PROGRESS = "agent:in-progress"
SHADOW_BRANCH_FMT = "shadow/issue-{n}"

# Default model for the planning step (orchestrator-side). Workers (Phase 4)
# pick their own model (opus for code, sonnet for r-w). Planning is a small
# prompt — sonnet is fast and cheap enough.
PLANNING_MODEL = "claude-sonnet-4-6"


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------

@dataclass
class Issue:
    number: int
    title: str
    body: str
    labels: List[str]


@dataclass
class PlanArtifacts:
    plan_md: str
    contract_md: str


# ---------------------------------------------------------------------------
# Shell helpers
# ---------------------------------------------------------------------------

def _run(cmd: List[str], *, check: bool = True, capture: bool = True,
         cwd: Optional[str] = None) -> subprocess.CompletedProcess:
    LOG.debug("$ %s", " ".join(cmd))
    return subprocess.run(
        cmd,
        check=check,
        capture_output=capture,
        text=True,
        cwd=cwd,
    )


# ---------------------------------------------------------------------------
# Kill-switch
# ---------------------------------------------------------------------------

def is_frozen() -> bool:
    """Read AGENT_FROZEN — true (any case) means halt this tick.

    The variable is passed in via env (vars.AGENT_FROZEN in the workflow).
    Unset / empty / 'false' all mean "not frozen".
    """
    raw = os.environ.get("AGENT_FROZEN", "").strip().lower()
    return raw in {"true", "1", "yes", "on"}


# ---------------------------------------------------------------------------
# Issue queue (real-mode via gh CLI)
# ---------------------------------------------------------------------------

def fetch_queue_issues(repo: str) -> List[Issue]:
    """Return open issues labelled `agent:queue`, oldest first."""
    proc = _run([
        "gh", "issue", "list",
        "--repo", repo,
        "--state", "open",
        "--label", LABEL_QUEUE,
        "--limit", "50",
        "--json", "number,title,body,labels",
    ])
    raw = json.loads(proc.stdout or "[]")
    issues: List[Issue] = []
    for entry in raw:
        labels = [label_obj["name"] for label_obj in entry.get("labels", [])]
        issues.append(Issue(
            number=entry["number"],
            title=entry["title"],
            body=entry.get("body") or "",
            labels=labels,
        ))
    # Oldest first — gh returns newest first by default, so reverse.
    issues.sort(key=lambda i: i.number)
    return issues


def pick_next_issue(issues: List[Issue]) -> Optional[Issue]:
    """Skip anything already in-progress; return the first remaining issue."""
    for issue in issues:
        if LABEL_IN_PROGRESS in issue.labels:
            continue
        return issue
    return None


# ---------------------------------------------------------------------------
# Branch management
# ---------------------------------------------------------------------------

def shadow_branch_name(issue_number: int) -> str:
    return SHADOW_BRANCH_FMT.format(n=issue_number)


def ensure_shadow_branch(issue_number: int, *, base: str = "main") -> str:
    """Create `shadow/issue-<n>` from `base` if it doesn't already exist."""
    branch = shadow_branch_name(issue_number)
    # Does the branch exist on the remote?
    proc = _run(["git", "ls-remote", "--heads", "origin", branch], check=False)
    exists_remote = bool(proc.stdout.strip())
    if exists_remote:
        LOG.info("shadow branch %s already exists on remote — reusing", branch)
        _run(["git", "fetch", "origin", branch])
        _run(["git", "checkout", "-B", branch, f"origin/{branch}"])
    else:
        LOG.info("creating shadow branch %s from %s", branch, base)
        _run(["git", "fetch", "origin", base])
        _run(["git", "checkout", "-B", branch, f"origin/{base}"])
    return branch


# ---------------------------------------------------------------------------
# Claude planning call
# ---------------------------------------------------------------------------

PLANNING_SYSTEM_PROMPT = """You are the planning step of an autonomous coding agent system.

You will be given an issue (Goal + Observable acceptance criteria). Produce two
markdown documents:

1. `plan.md` — a short numbered list of concrete subtasks. Each subtask must be
   either a "code" task (writes / edits Python source or tests) or a "rw" task
   (writes / edits markdown, docs, READMEs). Mark each subtask with `[code]` or
   `[rw]`. Keep the plan minimal — Simplicity First.

2. `contract.md` — the behavioral contract the validator will check the final
   PR against. Restate the Observable acceptance criteria. CRITICAL: contract.md
   describes observable behavior only. Do NOT name files, libraries, functions,
   classes, or algorithms. The independent validator must be able to judge the
   PR purely on what behavior the code exhibits, never on what it looks like.

Output format: a single JSON object with two string fields, plan_md and
contract_md. No prose outside the JSON.
"""


def plan_with_claude(issue: Issue) -> PlanArtifacts:
    """Call Claude to produce plan.md + contract.md for this issue.

    Tools available to Claude: NONE. This is a pure text-generation call; we
    intentionally do not give the planning step file-system or shell access
    (see docs/upgrade-plan.md §3.3 — orchestrator regulation).
    """
    # Import lazily so dry-run paths don't require anthropic to be installed.
    from anthropic import Anthropic  # type: ignore

    client = Anthropic()
    user_msg = textwrap.dedent(f"""
        Issue #{issue.number}: {issue.title}

        ---
        {issue.body}
        ---

        Produce plan.md and contract.md per the system prompt.
    """).strip()

    resp = client.messages.create(
        model=PLANNING_MODEL,
        max_tokens=4096,
        system=PLANNING_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    text = "".join(block.text for block in resp.content if block.type == "text").strip()

    # The model may wrap JSON in a ```json fence — strip it.
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[len("json"):].strip()
        if text.endswith("```"):
            text = text[: -len("```")].strip()

    data = json.loads(text)
    return PlanArtifacts(
        plan_md=data["plan_md"].strip() + "\n",
        contract_md=data["contract_md"].strip() + "\n",
    )


def plan_stub(issue: Issue) -> PlanArtifacts:
    """Deterministic plan used in --dry-run for local testing."""
    plan = textwrap.dedent(f"""
        # Plan for issue #{issue.number}: {issue.title}

        > Generated in dry-run mode — replace with real Claude output in production.

        1. [code] Implement the change requested by the Goal section of the issue.
        2. [rw] Document the change in the relevant README / docs.
    """).strip() + "\n"

    contract = textwrap.dedent(f"""
        # Contract for issue #{issue.number}

        > This contract is what the independent Gemini validator judges the final PR against.
        > It restates the Observable acceptance criteria from the issue body verbatim
        > and adds no new requirements.

        ## Observable acceptance criteria (from the issue)

        {issue.body or "_(issue body was empty — please re-file the issue with acceptance criteria)_"}
    """).strip() + "\n"

    return PlanArtifacts(plan_md=plan, contract_md=contract)


# ---------------------------------------------------------------------------
# Commit + push + label + comment
# ---------------------------------------------------------------------------

def commit_artifacts(branch: str, artifacts: PlanArtifacts,
                     issue_number: int) -> bool:
    """Write plan.md + contract.md to repo root, commit, push.

    Returns True if a commit was made, False if there was nothing to commit
    (e.g. the artifacts already match what's on the branch).
    """
    with open("plan.md", "w", encoding="utf-8") as f:
        f.write(artifacts.plan_md)
    with open("contract.md", "w", encoding="utf-8") as f:
        f.write(artifacts.contract_md)

    _run(["git", "add", "plan.md", "contract.md"])

    # Anything to commit?
    diff = _run(["git", "diff", "--cached", "--quiet"], check=False, capture=False)
    if diff.returncode == 0:
        LOG.info("no plan/contract changes to commit on %s", branch)
        return False

    _run([
        "git",
        "-c", "user.name=auto-evo orchestrator",
        "-c", "user.email=auto-evo@users.noreply.github.com",
        "commit", "-m",
        f"chore(orchestrator): plan + contract for issue #{issue_number}",
    ])
    _run(["git", "push", "origin", branch])
    return True


def mark_in_progress(repo: str, issue_number: int, plan_md: str) -> None:
    """Add the in-progress label and post the plan as a comment."""
    _run([
        "gh", "issue", "edit", str(issue_number),
        "--repo", repo,
        "--add-label", LABEL_IN_PROGRESS,
    ])

    branch = shadow_branch_name(issue_number)
    body = textwrap.dedent(f"""
        🤖 **Orchestrator picked this up.**

        Shadow branch: `{branch}`

        ---
        ## Plan

        {plan_md}
    """).strip()

    _run([
        "gh", "issue", "comment", str(issue_number),
        "--repo", repo,
        "--body", body,
    ])


# ---------------------------------------------------------------------------
# Tick entry point
# ---------------------------------------------------------------------------

def tick(repo: str, *, dry_run: bool) -> int:
    """Run one heartbeat tick. Returns process exit code."""
    if is_frozen():
        LOG.info("AGENT_FROZEN is set — halting this tick (kill-switch active)")
        return 0

    if dry_run:
        # Synthetic queue for local development.
        issues = [Issue(
            number=999,
            title="[agent] dry-run smoke task",
            body="Goal: prove the orchestrator tick runs end-to-end.\n\n"
                 "Observable acceptance criteria:\n"
                 "1. plan.md exists on the shadow branch.\n"
                 "2. contract.md exists on the shadow branch.",
            labels=[LABEL_QUEUE],
        )]
    else:
        issues = fetch_queue_issues(repo)

    chosen = pick_next_issue(issues)
    if chosen is None:
        LOG.info("queue empty (or all in-progress) — nothing to do this tick")
        return 0

    LOG.info("picked issue #%d: %s", chosen.number, chosen.title)

    if dry_run:
        # Don't touch git or gh in dry-run; just confirm the plan flow.
        artifacts = plan_stub(chosen)
        LOG.info("dry-run plan.md (%d chars), contract.md (%d chars)",
                 len(artifacts.plan_md), len(artifacts.contract_md))
        return 0

    branch = ensure_shadow_branch(chosen.number)
    artifacts = plan_with_claude(chosen)
    commit_artifacts(branch, artifacts, chosen.number)
    mark_in_progress(repo, chosen.number, artifacts.plan_md)

    LOG.info("tick complete for issue #%d on %s", chosen.number, branch)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="One orchestrator heartbeat tick")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""),
                        help="owner/repo (defaults to $GITHUB_REPOSITORY)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Skip gh + Anthropic calls; exercise control flow only.")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if not args.dry_run and not args.repo:
        parser.error("--repo is required when not running in --dry-run")

    return tick(args.repo, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
