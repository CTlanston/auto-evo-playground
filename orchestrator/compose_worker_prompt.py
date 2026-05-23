"""Compose the prompt sent to anthropics/claude-code-action for a worker job.

Called from worker.yml. CLI signature is locked to what the YAML invokes; do
not change without updating .github/workflows/worker.yml.
"""
from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path

KIND_DESCRIPTIONS = {
    "code": (
        "You are a CODE worker. You write or edit Python source files and tests. "
        "You may not modify documentation files (README.md, docs/**, *.md other "
        "than the done.md you produce). Stay narrowly scoped to the subtask below."
    ),
    "rw": (
        "You are a READ-WRITE (documentation) worker. You write or edit Markdown "
        "documentation: README.md, files under docs/, and similar. You may not "
        "edit Python source files or tests. Stay narrowly scoped to the subtask below."
    ),
}


def build_prompt(*, kind: str, name: str, issue: str, branch: str, subtask: str) -> str:
    role = KIND_DESCRIPTIONS.get(kind)
    if role is None:
        raise SystemExit(f"unknown worker kind: {kind!r} (expected 'code' or 'rw')")

    return textwrap.dedent(f"""
        You are working on a self-evolving codebase that loads CLAUDE.md at the
        repository root. You have already loaded the nine behavioral rules in
        that file — apply them. In particular: Simplicity First, Surgical
        Changes, Goal-Driven Execution, and (rule 6) NEVER touch the control
        plane (.github/workflows, orchestrator/, validator/, CLAUDE.md,
        .github/CODEOWNERS).

        ## Your role

        {role}

        ## Context

        - Issue number: #{issue}
        - Branch: {branch} (already checked out)
        - Worker name: {name}
        - Worker kind: {kind}

        Read `plan.md` and `contract.md` from the repository root for the full
        plan and the behavioral contract this issue will be judged against.

        ## Your subtask

        {subtask}

        ## What "done" means for you

        1. Implement exactly what the subtask requires — nothing more.
        2. Run any narrow checks you can to confirm your change works. The full
           test suite runs separately in shadow-ci.yml with no secrets; do NOT
           run network calls, do NOT export environment variables, do NOT echo
           any value that looks like a credential.
        3. Write `workers/{name}/done.md` (create the directory). The file must contain:
           - **What I produced** — a short list of files touched and why.
           - **How to verify it** — one or more behavioral checks the validator
             can perform without reading source code (e.g. a `pytest` invocation,
             a function call and expected return value, an artifact that must
             exist). These checks must align with `contract.md`.
        4. Do NOT commit. The workflow step after you handles git.

        Begin.
    """).strip() + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Compose a worker prompt for claude-code-action")
    parser.add_argument("--kind", required=True, choices=["code", "rw"])
    parser.add_argument("--name", required=True)
    parser.add_argument("--issue", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--subtask-file", required=True,
                        help="Path to a file (or process substitution) containing the subtask text.")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    subtask = Path(args.subtask_file).read_text(encoding="utf-8").strip()
    prompt = build_prompt(
        kind=args.kind,
        name=args.name,
        issue=args.issue,
        branch=args.branch,
        subtask=subtask,
    )
    Path(args.out).write_text(prompt, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
