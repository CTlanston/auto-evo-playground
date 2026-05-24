# code-1 — done

## What I produced
- `src/mathx.py` — new module exposing two integer-arithmetic functions:
  - `add(a, b)` returns `a + b`
  - `mul(a, b)` returns `a * b`

No other files were touched. README and tests are owned by sibling subtasks per `plan.md`.

## How to verify it
Behavioral checks aligned to `contract.md` items 2–4 (item 1 depends on the test file authored by another worker, item 5 on the README worker):

1. Import succeeds:
   ```
   python -c "from src.mathx import add, mul"
   ```
   Exits 0.

2. `add` behavior:
   ```
   python -c "from src.mathx import add; assert add(2, 3) == 5; assert add(-2, 3) == 1"
   ```
   Exits 0.

3. `mul` behavior:
   ```
   python -c "from src.mathx import mul; assert mul(4, 5) == 20; assert mul(-2, 3) == -6"
   ```
   Exits 0.

4. File exists:
   ```
   test -f src/mathx.py
   ```
   Exits 0.
