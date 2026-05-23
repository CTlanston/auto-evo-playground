"""Heterologous validator entry point.

Run from .github/workflows/validator.yml. Collects behavioral evidence
(contract, done.md, file manifest, test-results summaries) for a given PR,
sends it to Gemini 2.5 Pro, and writes:
  - a PR comment with the verdict
  - a check named `heterologous-validation` with PASS/FAIL conclusion

Hard rules (enforced by code, not just convention):
  * We do NOT checkout the PR head's source code.
  * We do NOT read PR file contents — only path + size + line counts.
  * We do NOT include full test failure stack traces — only failing test names.

See docs/upgrade-plan.md §5 and validator/prompt.md.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from xml.etree import ElementTree as ET

LOG = logging.getLogger("validator.validate")

MODEL = "gemini-2.5-pro"
CHECK_NAME = "heterologous-validation"
PROMPT_PATH = Path(__file__).parent / "prompt.md"


# ---------------------------------------------------------------------------
# Evidence types
# ---------------------------------------------------------------------------

@dataclass
class FileEntry:
    path: str
    additions: int
    deletions: int


@dataclass
class TestSummary:
    # Tell pytest not to collect this dataclass as a test class.
    __test__ = False

    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    failing_names: List[str] = field(default_factory=list)


@dataclass
class Evidence:
    contract_md: str
    done_reports: Dict[str, str]   # worker name -> done.md content
    file_manifest: List[FileEntry]
    test_summaries: Dict[str, TestSummary]   # artifact name -> summary


# ---------------------------------------------------------------------------
# Evidence collection — uses gh CLI + local workdir; never reads PR source.
# ---------------------------------------------------------------------------

def _run(cmd: List[str], *, check: bool = True,
         capture: bool = True) -> subprocess.CompletedProcess:
    LOG.debug("$ %s", " ".join(cmd))
    return subprocess.run(cmd, check=check, capture_output=capture, text=True)


def fetch_contract_and_done(repo: str, branch: str) -> tuple[str, Dict[str, str]]:
    """Fetch contract.md and all workers/*/done.md from the PR's head branch.

    These ARE the only branch files we ever read — they're explicitly behavioral
    artifacts the worker produced for the validator, not implementation source.
    """
    contract = _safe_git_show(branch, "contract.md") or ""

    # List all done.md files under workers/
    proc = subprocess.run(
        ["git", "ls-tree", "-r", f"origin/{branch}", "--name-only"],
        check=True, capture_output=True, text=True,
    )
    done_paths = [
        line for line in proc.stdout.splitlines()
        if line.startswith("workers/") and line.endswith("/done.md")
    ]
    done_reports: Dict[str, str] = {}
    for path in done_paths:
        worker_name = path.split("/")[1]
        body = _safe_git_show(branch, path) or ""
        done_reports[worker_name] = body
    return contract, done_reports


def _safe_git_show(branch: str, path: str) -> Optional[str]:
    proc = subprocess.run(
        ["git", "show", f"origin/{branch}:{path}"],
        check=False, capture_output=True, text=True,
    )
    return proc.stdout if proc.returncode == 0 else None


def fetch_file_manifest(repo: str, pr_number: int) -> List[FileEntry]:
    """List files changed in the PR. Path + additions + deletions only.

    NO file content. We deliberately use `gh pr view --json files` which
    returns metadata, not patch text.
    """
    proc = _run([
        "gh", "pr", "view", str(pr_number),
        "--repo", repo,
        "--json", "files",
    ])
    raw = json.loads(proc.stdout or "{}")
    files = raw.get("files", []) or []
    out: List[FileEntry] = []
    for f in files:
        out.append(FileEntry(
            path=f["path"],
            additions=f.get("additions", 0),
            deletions=f.get("deletions", 0),
        ))
    return out


def fetch_test_summaries(repo: str, run_id: Optional[str], workdir: Path) -> Dict[str, TestSummary]:
    """Download shadow-ci artifacts and parse junit-*.xml summaries.

    We do NOT read full test source or stack traces — only:
      - aggregate counts (passed/failed/skipped/errors)
      - failing test names (helpful diagnostic, no source)
    """
    if not run_id:
        LOG.info("no shadow-ci run id provided — skipping test summaries")
        return {}

    workdir.mkdir(parents=True, exist_ok=True)
    artifact_names = ["test-results-fast", "test-results-integration", "test-results-coverage"]
    summaries: Dict[str, TestSummary] = {}
    for name in artifact_names:
        target = workdir / name
        target.mkdir(parents=True, exist_ok=True)
        rc = subprocess.run(
            ["gh", "run", "download", run_id, "--repo", repo,
             "--name", name, "--dir", str(target)],
            check=False, capture_output=True, text=True,
        )
        if rc.returncode != 0:
            LOG.info("artifact %s not available (run %s): %s",
                     name, run_id, rc.stderr.strip())
            continue
        summary = _parse_junit_dir(target)
        summaries[name] = summary
    return summaries


def _parse_junit_dir(directory: Path) -> TestSummary:
    """Sum a directory of JUnit XML files into one TestSummary. Names only — no traces."""
    s = TestSummary()
    for xml in directory.glob("junit-*.xml"):
        try:
            tree = ET.parse(xml)
        except ET.ParseError:
            continue
        for testsuite in tree.iter("testsuite"):
            s.passed += int(testsuite.get("tests", 0)) - int(testsuite.get("failures", 0)) \
                - int(testsuite.get("errors", 0)) - int(testsuite.get("skipped", 0))
            s.failed += int(testsuite.get("failures", 0))
            s.errors += int(testsuite.get("errors", 0))
            s.skipped += int(testsuite.get("skipped", 0))
        for case in tree.iter("testcase"):
            if case.find("failure") is not None or case.find("error") is not None:
                # Names only — never include the failure message or stack trace.
                cls = case.get("classname", "")
                name = case.get("name", "")
                s.failing_names.append(f"{cls}::{name}" if cls else name)
    return s


# ---------------------------------------------------------------------------
# Prompt construction & Gemini call
# ---------------------------------------------------------------------------

def format_evidence(ev: Evidence) -> str:
    """Render Evidence into the text block sent to Gemini.

    Path-and-size only for files; counts and names only for tests; full text
    for contract.md and done.md (those are explicitly behavioral artifacts).
    """
    out = []
    out.append("# contract.md\n")
    out.append(ev.contract_md.strip() or "_(missing)_")

    out.append("\n\n# workers/*/done.md\n")
    if not ev.done_reports:
        out.append("_(no done.md files found on the PR branch)_")
    else:
        for name, body in sorted(ev.done_reports.items()):
            out.append(f"\n## workers/{name}/done.md\n")
            out.append(body.strip() or "_(empty)_")

    out.append("\n\n# File change manifest (paths + line counts only — no content)\n")
    if not ev.file_manifest:
        out.append("_(no files changed)_")
    else:
        for f in ev.file_manifest:
            out.append(f"- `{f.path}` (+{f.additions}/-{f.deletions})")

    out.append("\n\n# Test results (summaries only — no stack traces)\n")
    if not ev.test_summaries:
        out.append("_(no shadow-ci artifacts available)_")
    else:
        for artifact, s in ev.test_summaries.items():
            out.append(f"\n## {artifact}")
            out.append(f"- passed: {s.passed}")
            out.append(f"- failed: {s.failed}")
            out.append(f"- errors: {s.errors}")
            out.append(f"- skipped: {s.skipped}")
            if s.failing_names:
                out.append("- failing test names:")
                for n in s.failing_names:
                    out.append(f"  - `{n}`")
    return "\n".join(out)


def call_gemini(prompt_system: str, evidence_text: str, *, mock: bool = False) -> str:
    """Send (system, evidence) to gemini-2.5-pro and return the raw response.

    In mock mode we synthesize a deterministic PASS/FAIL based purely on the
    evidence so the workflow can be tested without API access.
    """
    if mock:
        return _mock_verdict(evidence_text)

    # Lazy import — keeps mock-mode runnable without google-genai installed.
    from google import genai  # type: ignore

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    resp = client.models.generate_content(
        model=MODEL,
        contents=[
            {"role": "user", "parts": [{"text": prompt_system}]},
            {"role": "user", "parts": [{"text": evidence_text}]},
        ],
    )
    return resp.text


def _mock_verdict(evidence_text: str) -> str:
    """Tiny rule: PASS iff no failing tests and at least one done.md and contract not empty."""
    failing = "failed: 0" in evidence_text and "errors: 0" in evidence_text
    has_done = "## workers/" in evidence_text
    has_contract = "_(missing)_" not in evidence_text.split("# workers/*/done.md")[0]
    if failing and has_done and has_contract:
        return (
            "PASS\n"
            "---\n"
            "Reasons:\n"
            "- Mock validator: contract present, at least one worker reported done, "
            "and no failing tests in summaries.\n"
        )
    return (
        "FAIL\n"
        "---\n"
        "Reasons:\n"
        "- Mock validator: missing contract, or no done.md, or failing tests detected.\n"
        "Remediation:\n"
        "- Provide contract.md, workers/*/done.md, and ensure shadow-ci runs are green.\n"
    )


# ---------------------------------------------------------------------------
# Verdict publication: PR comment + GitHub check
# ---------------------------------------------------------------------------

def parse_conclusion(verdict_text: str) -> str:
    first = verdict_text.strip().splitlines()[0].strip().upper() if verdict_text.strip() else ""
    if first.startswith("PASS"):
        return "success"
    if first.startswith("FAIL"):
        return "failure"
    return "neutral"


def publish_verdict(repo: str, pr_number: int, head_sha: str,
                    verdict_text: str) -> None:
    """Post the verdict to the PR and set a check status."""
    # PR comment.
    body = textwrap.dedent(f"""
        🧑‍⚖️ **Heterologous validation** (gemini-2.5-pro, never saw the source)

        ```
        {verdict_text.strip()}
        ```
    """).strip()
    _run([
        "gh", "pr", "comment", str(pr_number),
        "--repo", repo,
        "--body", body,
    ], check=False)

    # GitHub check (commit status form — simpler than the Checks API for our needs).
    conclusion = parse_conclusion(verdict_text)
    state = {"success": "success", "failure": "failure"}.get(conclusion, "error")
    _run([
        "gh", "api",
        "--method", "POST",
        f"repos/{repo}/statuses/{head_sha}",
        "-f", f"state={state}",
        "-f", f"context={CHECK_NAME}",
        "-f", f"description=Verdict: {state}",
    ], check=False)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def validate(*, repo: str, pr_number: int, branch: str,
             head_sha: str, shadow_run_id: Optional[str],
             workdir: Path, mock: bool) -> int:
    contract, done = fetch_contract_and_done(repo, branch)
    manifest = fetch_file_manifest(repo, pr_number)
    summaries = fetch_test_summaries(repo, shadow_run_id, workdir)
    ev = Evidence(
        contract_md=contract,
        done_reports=done,
        file_manifest=manifest,
        test_summaries=summaries,
    )
    prompt_system = PROMPT_PATH.read_text(encoding="utf-8")
    evidence_text = format_evidence(ev)
    verdict = call_gemini(prompt_system, evidence_text, mock=mock)
    LOG.info("verdict:\n%s", verdict)
    publish_verdict(repo, pr_number, head_sha, verdict)
    return 0 if parse_conclusion(verdict) == "success" else 1


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Heterologous validation entry")
    p.add_argument("--repo", required=True)
    p.add_argument("--pr", type=int, required=True, dest="pr_number")
    p.add_argument("--branch", required=True, help="PR head branch (e.g. shadow/issue-42)")
    p.add_argument("--head-sha", required=True)
    p.add_argument("--shadow-run-id", default=None,
                   help="Workflow run id of the shadow-ci that produced test-results artifacts.")
    p.add_argument("--workdir", default="validator-evidence",
                   help="Directory for downloaded artifacts. Wiped on each run.")
    p.add_argument("--mock", action="store_true",
                   help="Skip Gemini API call; synthesize a verdict from evidence.")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    return validate(
        repo=args.repo,
        pr_number=args.pr_number,
        branch=args.branch,
        head_sha=args.head_sha,
        shadow_run_id=args.shadow_run_id,
        workdir=Path(args.workdir),
        mock=args.mock,
    )


if __name__ == "__main__":
    sys.exit(main())
