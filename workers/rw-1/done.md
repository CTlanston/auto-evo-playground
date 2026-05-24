# rw-1 done

## What I produced

- **`README.md`** — added a `## mathx` section that documents both `add` and `mul` with example usage.

## How to verify it

1. `grep -n "mathx" README.md` — should show the new section heading and inline references.
2. `grep -n "add" README.md` and `grep -n "mul" README.md` — both symbols must appear in the file.
3. Contract criterion 5: the section exists, names both `add` and `mul`, and gives a concrete usage example.
