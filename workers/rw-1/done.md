# rw-1 done

## What I produced

- **`README.md`** — appended the line `validator-fail-smoke: present` at the end of the file (after the Local development section). No other files were touched.

## How to verify it

```bash
grep -c "validator-fail-smoke: present" README.md
# expected output: 1
```

Per `contract.md`, the contract is intentionally contradictory (criterion 1 requires the string present; criterion 2 requires it absent), so validation is expected to fail as a smoke test of the validator's ability to reject contradictory contracts.
