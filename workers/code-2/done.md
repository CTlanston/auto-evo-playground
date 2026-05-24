# code-2 done

## What I produced

- `tests/test_mathx.py` — new pytest module with four test cases covering the behavioral checks for `add` and `mul` from the contract:
  - `test_add_positive`: `add(2, 3) == 5`
  - `test_add_negative`: `add(-2, 3) == 1`
  - `test_mul_positive`: `mul(4, 5) == 20`
  - `test_mul_negative`: `mul(-2, 3) == -6`

## How to verify it

From the repository root, run:

```
pytest tests/test_mathx.py -q
```

Expected: exit code 0, four tests collected and passing. This satisfies acceptance criterion 1 in `contract.md` and exercises criteria 2–4 (import and return values for `add`/`mul`).
