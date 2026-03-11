# Self-Healing CI - Loop Flow Details

## Agent Coordination

Uses TaskCreate with blockedBy dependencies:

1. Task "implement": implementer writes code per spec
2. Task "test-round-N": tester runs suite (blockedBy: implement or fix-round-N-1)
3. Task "fix-round-N": fixer patches failures (blockedBy: test-round-N)
4. Loop test->fix until GREEN or max iterations reached

## Iteration Limits

- Default: 5 iterations maximum
- Configurable via `--max-iterations N`
- On max iterations without green: report last failure state, do NOT commit

## Commit Behavior

- `--auto-commit`: Commit automatically when tests pass
- Commit message: `feat(<scope>): <spec summary> [self-heal: N iterations]`
- Without flag: report success but let user decide on commit

## Abort Conditions

- Build/compile errors that prevent test execution: report and stop
- Same failure persists for 3 consecutive iterations: likely design issue, stop and report
- No test files found: ask user for test location
