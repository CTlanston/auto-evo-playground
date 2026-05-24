# auto-evo-playground

A self-evolving Python codebase driven by Claude + judged by Gemini, with all orchestration on plain GitHub Actions. The full design lives in [`docs/upgrade-plan.md`](docs/upgrade-plan.md) — start there.

## What this is

You file an issue with a goal + acceptance criteria. A scheduled GitHub Actions cron picks it up, opens a shadow branch, asks Claude to draft a plan + behavioral contract, dispatches workers (code + r/w) that implement against the plan, runs CI, and submits the PR to an **independent Gemini validator** that has never seen your source code. Only when the validator says PASS and CI is green does the PR auto-merge.

```
agent:queue issue
        │
        ▼
[orchestrator schedule cron]  ─►  plan.md + contract.md  ─►  workers (opus/sonnet)
        │                                                        │
        │                                                        ▼
        │                                              shadow-ci (no secrets)
        │                                                        │
        ▼                                                        ▼
[orchestrator: all workers done?] ─yes─►  PR  ─►  validator (Gemini, never sees source)
                                                                 │
                                                                 ▼
                                                       PASS + CI green
                                                                 │
                                                                 ▼
                                                          auto-merge.yml
                                                                 │
                                                                 ▼
                                                       squash → main + close issue
```

The whole control plane is in `.github/workflows/`, `orchestrator/`, and `validator/`. Those paths are CODEOWNERS-protected; agents are forbidden from modifying them ([CLAUDE.md](CLAUDE.md) rule 6).

## Layout

| Path | Purpose | Who can edit |
|---|---|---|
| `CLAUDE.md` | Behavioral contract auto-loaded by every Claude job | CODEOWNER only |
| `.github/workflows/orchestrator.yml` | Heartbeat (schedule cron + workflow_dispatch) | CODEOWNER only |
| `.github/workflows/worker.yml` | Code/RW worker — runs Claude Code Action | CODEOWNER only |
| `.github/workflows/shadow-ci.yml` | No-secret CI: fast lane + slow lane | CODEOWNER only |
| `.github/workflows/validator.yml` | Heterologous Gemini judge | CODEOWNER only |
| `.github/workflows/auto-merge.yml` | Guard-rail squash-merge on green | CODEOWNER only |
| `.github/workflows/revert.yml` | Emergency rollback (opens revert PR) | CODEOWNER only |
| `.github/workflows/daily-digest.yml` | Daily activity summary | CODEOWNER only |
| `.github/workflows/watchdog.yml` | Hourly stuck-state detector | CODEOWNER only |
| `.github/ISSUE_TEMPLATE/agent-task.yml` | The form everyone uses to file work | CODEOWNER only |
| `orchestrator/` | tick / dispatch / digest / watchdog code | CODEOWNER only |
| `validator/` | Gemini validator code + prompt | CODEOWNER only |
| `src/` | The actual evolving codebase | Agents write here |
| `tests/test_*.py` (general) | Agent-written tests | Agents write here |
| `tests/test_orchestrator_*.py`, `tests/test_validator_*.py` | Tests of the control plane | CODEOWNER only |

## Bringing it up (one-time GitHub-side configuration)

Everything in the repo is set up; the items below are the things you must do on GitHub itself before the agent can run.

1. **Create labels** (one-shot, `gh` from any clone):
   ```bash
   gh label create agent:queue       --description "Awaiting orchestrator pickup" --color "ededed"
   gh label create agent:in-progress --description "Workers dispatched"           --color "fbca04"
   gh label create agent:done        --description "PR merged"                    --color "0e8a16"
   gh label create agent:blocked     --description "Watchdog flagged stuck"       --color "d93f0b"
   ```

2. **Create the repository variable** that drives the kill switch:
   ```bash
   gh variable set AGENT_FROZEN --body "false"
   ```
   Flip to `true` (in Settings → Variables, or `gh variable set AGENT_FROZEN --body "true"`) to halt the orchestrator instantly.

3. **Create secrets** (Settings → Secrets and variables → Actions):
   - `ANTHROPIC_API_KEY` — for orchestrator planning + worker execution
   - `GEMINI_API_KEY` — for the heterologous validator (must be a different account / scope from Anthropic's)
   - `AGENT_PAT` — a **fine-grained personal access token** for the agent. Scope to this repo only, with `Contents: read & write`, `Issues: read & write`, `Pull requests: read & write`, `Actions: read & write`. Default `${{ secrets.GITHUB_TOKEN }}` will not work because it cannot trigger downstream workflows (`workflow_dispatch`).

4. **Configure branch protection on `main`** (Settings → Branches → Add rule):
   - Require a pull request before merging
   - Require status checks: `heterologous-validation`, `fast-lint`, `fast-unit`
   - Require review from CODEOWNERS
   - Restrict pushes; only the agent (via squash-merge from auto-merge.yml) and CODEOWNERS may merge
   - **Confirm** `main` has no deploy step — this repo treats main as the durable record, not a deploy target.

5. **(Optional)** Pin the orchestrator schedule to a tighter cadence in `.github/workflows/orchestrator.yml` (default: every 15 min).

## End-to-end smoke test (Phase 9 acceptance)

Once the configuration above is in place, file this seed issue to verify the full pipeline. Use the **Agent task** issue template:

> **Title:** `[agent] add mathx.add and mathx.mul with tests`
>
> **Goal:** Add a `mathx` module with two pure functions, `add(a, b)` and `mul(a, b)`, returning numeric sums and products respectively.
>
> **Observable acceptance criteria:**
> 1. `pytest tests/test_mathx.py -q` exits 0.
> 2. `from src.mathx import add, mul` succeeds.
> 3. `add(2, 3)` returns `5`; `add(-1, 1)` returns `0`.
> 4. `mul(2, 3)` returns `6`; `mul(0, 999)` returns `0`.
> 5. The functions handle floats: `add(1.5, 2.5)` returns `4.0`.
>
> **Scope limits:** Do not modify any existing file under `src/` or `tests/` other than the two new files implied above.

Expected timeline (rough): orchestrator picks up within 15 min, plan/contract pushed within 2 min, workers complete within ~5 min, shadow-ci green within 2 min, validator PASS within 1 min, auto-merge fires immediately. Total: under 20 min from issue creation to merge.

If the smoke fails, the digest issue (`[auto-evo] Daily digest`) and the watchdog comments will surface where it stuck.

## mathx

`src/mathx.py` exposes two pure arithmetic helpers:

```python
from src.mathx import add, mul

add(2, 3)   # → 5
mul(4, 5)   # → 20
```

`add(a, b)` returns the sum and `mul(a, b)` returns the product.

## Local development

```bash
# Sanity check the control flow without secrets:
python3 -m orchestrator.tick --dry-run --verbose
AGENT_FROZEN=true python3 -m orchestrator.tick --dry-run    # kill-switch demo
python3 -m pytest tests/test_orchestrator_*.py tests/test_validator_*.py --no-cov -q
```

The control-plane tests do not need any external services or secrets. The agent-written tests under `tests/` may.

validator-fail-smoke: present
