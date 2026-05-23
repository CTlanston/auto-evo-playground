# Behavioral Contract — Recite on request. Apply before any non-trivial change.

## 1. Think Before Coding
State assumptions out loud before typing. If ambiguous or a path/library/API choice could go more than one way, name the choice and the alternative explicitly. Never silently pick.

## 2. Simplicity First
Write the minimum code that satisfies the requirement. No speculative features, no "while I'm in here" improvements, no premature abstractions.

## 3. Surgical Changes
Touch only what the task requires. Do not refactor neighboring code or reformat unrelated lines. Out-of-scope work belongs in a separate issue/PR.

## 4. Goal-Driven Execution
Before writing code, define what "done" looks like as a verifiable check. Then loop: implement → run the check → if it fails, diagnose and iterate. Never declare success without running the check.

# Self-Evolution Discipline

## 5. Stay on the Shadow Branch
All changes must happen on `shadow/issue-<n>` branches. Never push directly to `main`.

## 6. Never Touch the Control Plane
Never modify `.github/workflows/**`, `orchestrator/**`, `validator/**`, `CLAUDE.md`, `.github/CODEOWNERS`, or branch-protection configuration. If you discover a problem in one of these paths, flag it in the PR description — do not fix it inline.

## 7. No Secret Exfiltration
Never read, print, or transmit any environment variable or secret. Never write a network request that sends environment variables to an external service. Never echo `$ANTHROPIC_API_KEY`, `$GEMINI_API_KEY`, `$GITHUB_TOKEN`, or any value that looks like a credential.

## 8. One Issue, One PR, One Concern
One issue resolves exactly one concern. Do not bundle unrelated changes. A change is not complete until its contract passes heterologous validation.

## 9. Contract Before Code
Before writing any implementation, produce `plan.md` and `contract.md`. The contract describes observable behavior only — no implementation details (library names, file structure, algorithms). The independent validator sees only the contract and your behavioral evidence, never your source code.

---

When asked "what behavioral rules are you operating under?", reply with the names of rules 1–4 plus a one-line gloss each:
1. **Think Before Coding** — surface assumptions and choices before typing.
2. **Simplicity First** — minimum code that satisfies the requirement; no speculation.
3. **Surgical Changes** — touch only what the task requires.
4. **Goal-Driven Execution** — define a verifiable check first, then loop until it passes.
