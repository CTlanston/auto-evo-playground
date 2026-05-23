"""Tests for orchestrator.dispatch.parse_plan — plan.md → Subtask list."""
from orchestrator.dispatch import Subtask, parse_plan


def test_parses_numbered_code_and_rw():
    plan = """
    # Plan

    1. [code] Implement reverse_string in src/utils.py.
    2. [rw] Document reverse_string in README.md.
    3. [code] Add tests/test_reverse_string.py.
    """
    subs = parse_plan(plan)
    assert subs == [
        Subtask(kind="code", name="code-1", text="Implement reverse_string in src/utils.py."),
        Subtask(kind="rw",   name="rw-1",   text="Document reverse_string in README.md."),
        Subtask(kind="code", name="code-2", text="Add tests/test_reverse_string.py."),
    ]


def test_ignores_titles_and_prose():
    plan = """
    # Plan for issue 42

    Some preamble paragraph that should be ignored.

    - [code] Do the thing.

    > Blockquote — ignored.
    """
    subs = parse_plan(plan)
    assert subs == [Subtask(kind="code", name="code-1", text="Do the thing.")]


def test_kind_tag_case_insensitive():
    plan = "1. [CODE] big tag.\n2. [Rw] mixed.\n"
    subs = parse_plan(plan)
    assert [s.kind for s in subs] == ["code", "rw"]


def test_empty_plan_returns_empty_list():
    assert parse_plan("") == []
    assert parse_plan("# Just a heading\n\nNo subtasks here.\n") == []


def test_dispatch_naming_separates_code_and_rw_counters():
    """code-1, code-2 ... and rw-1, rw-2 ... are independent counters."""
    plan = """
    1. [code] a
    2. [rw] b
    3. [code] c
    4. [rw] d
    5. [rw] e
    """
    subs = parse_plan(plan)
    assert [s.name for s in subs] == ["code-1", "rw-1", "code-2", "rw-2", "rw-3"]
