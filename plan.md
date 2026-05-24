# Plan

## Assumptions

- Issue #40 tracks the current issue-template blocker.
- The GitHub chooser is not indexing the YAML issue form even though the file exists on `main`.
- The smallest useful fix is to make the form match GitHub's documented examples more closely before falling back to command-line issue creation.

## Steps

- [code] Simplify the Agent task issue form so GitHub's template indexer has fewer edge cases to reject.
- [code] Update the worker workflow to use Claude Code Action v1 inputs documented by the action.
- [code] Validate the YAML locally.
- [rw] After user approval, push the branch and verify the form appears in GitHub's template chooser.
- [rw] If the form still does not appear, create the smoke-test issue directly with `gh issue create --label agent:queue`.

## Done Check

- `.github/ISSUE_TEMPLATE/agent_task.yml` parses as YAML.
- The template has `name`, `description`, and `body` top-level fields.
- The template retains required fields for goal and observable acceptance criteria.
- `worker.yml` passes the composed worker instructions through the action's `prompt` input and model selection through `claude_args`.
- After push, GitHub lists the template in the issue chooser or the smoke-test issue is created by CLI with `agent:queue`.
