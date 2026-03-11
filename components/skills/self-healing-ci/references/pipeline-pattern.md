# Pipeline Pattern — Validated Multi-Stage Execution

## Core Concept

A pipeline chains stages sequentially. Each stage:
1. Reads the previous stage's output from `.agent-status/<stage>.json`
2. Does its work
3. Writes structured results to `.agent-status/<stage>.json`
4. Reports PASS or FAIL with details

The orchestrator (lead agent) checks each stage before advancing.

## Stage Contract

Every stage writes JSON output:

```json
{
  "stage": "implement",
  "status": "pass",
  "timestamp": "2026-03-02T21:30:00Z",
  "files_changed": ["src/auth.py", "tests/test_auth.py"],
  "summary": "Added JWT validation with 3 new tests",
  "details": {},
  "errors": []
}
```

Status values: `pass`, `fail`, `skip`

## Built-in Stages

### 1. Implement
- Input: spec/description from user
- Work: write code + unit tests
- Output: files changed, test results
- On fail: retry via self-healing CI inner loop (max 5 iterations)
- Pass criteria: all unit tests green

### 2. Test Validation
- Input: implement stage output (files_changed)
- Work: run FULL test suite (not just new tests), check for regressions
- Output: total passed/failed/skipped, any regressions
- On fail: hand regression details back to implementer for fix
- Pass criteria: no regressions, all tests pass

### 3. Security Check
- Input: implement stage output (files_changed)
- Work: run bandit/safety on changed files, check for secrets, OWASP patterns
- Output: findings classified P0/P1/P2
- On fail (P0): stop pipeline, report to user
- On fail (P1/P2): auto-fix if possible, report remaining
- Pass criteria: no P0, all P1 auto-fixed or documented

### 4. Validate & Commit
- Input: all previous stage outputs
- Work: verify all stages passed, create commit
- Output: commit hash, summary
- On fail: create remediation tasks, do NOT commit
- Pass criteria: all upstream stages PASS

## Retry Logic

- Each stage gets 1 automatic retry on failure
- If retry fails: escalate to user with diagnostics
- Exception: implement stage uses self-healing CI loop (up to 5 retries)

## Handoff Format

Stages communicate via `.agent-status/` directory:
```
.agent-status/
  pipeline-meta.json    # pipeline ID, start time, spec
  implement.json        # stage 1 output
  test-validation.json  # stage 2 output
  security-check.json   # stage 3 output
  validate-commit.json  # stage 4 output
```

## Abort Conditions

- Any stage fails after retry: pipeline halts, user notified
- P0 security finding: immediate halt
- Same error 3 times across stages: design issue, stop and report
- Pipeline timeout: configurable, default none
