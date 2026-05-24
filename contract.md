# Behavioral Contract

## Acceptance Criteria

1. Running `pytest tests/test_mathx.py -q` exits with code 0 (all tests pass).
2. The import `from src.mathx import add, mul` succeeds without error.
3. `add(2, 3)` returns `5`; `add(-2, 3)` returns `1`.
4. `mul(4, 5)` returns `20`; `mul(-2, 3)` returns `-6`.
5. `README.md` contains a section or note about `mathx` that mentions both `add` and `mul`.
