# Contract

The repository provides a usable Agent task entry point for the self-evolving workflow.

Observable acceptance criteria:

1. GitHub offers an "Agent task" issue template in the repository's new issue chooser, or a maintainer can create an equivalent queued agent issue with `gh issue create`.
2. An agent issue created through the supported path includes a goal field and observable acceptance criteria.
3. A queued agent issue carries the `agent:queue` label so the orchestrator can pick it up.
4. The issue-template YAML parses successfully.
