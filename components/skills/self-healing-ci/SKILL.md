---
name: self-healing-ci
description: 3-agent write-test-fix loop that iterates until tests pass. Implementer writes code, tester validates, fixer patches failures. Max 5 iterations, commits on green.
requires:
  bins: []  # test runner auto-detected: pytest (Python), npm test (Node), cargo test (Rust)
# Context cost: ~68 lines (~1.5K tokens). References: references/loop-flow.md
---

# Self-Healing CI

Autonomous code implementation loop using 3 coordinated agents that iterate until all tests pass.

## Agent Roles

### 1. Implementer
- Writes code based on the provided spec/description
- Creates new files or modifies existing ones
- Follows project conventions (detected from CLAUDE.md, existing code)
- On subsequent iterations: applies fixer's patches

### 2. Tester
- Runs the full test suite after implementer finishes
- Detects test runner: pytest (Python), npm test (Node), cargo test (Rust)
- Reports: pass count, fail count, failure details with stack traces
- Verdict: GREEN (all pass) or RED (failures exist)

### 3. Fixer
- Receives tester's failure report
- Analyzes stack traces and test output
- Produces targeted, minimal fixes — not rewrites
- Hands back to tester for re-validation

## Loop Flow

```
Implementer → Tester → [GREEN? → Commit] or [RED? → Fixer → Tester → ...]
```

## Initializer/Coder Split (Optional Enhancement)

For larger features where test scaffolding and implementation are distinct concerns,
split the Implementer role into two sequential sub-phases before entering the loop:

### Sub-phase A: Initializer
- Reads the spec and existing code structure
- Creates the file skeleton (empty classes, function stubs, `raise NotImplementedError`)
- Writes test stubs: test file with all test function names and docstrings, but `assert False` bodies
- Does NOT implement logic — only establishes structure and contracts
- Outputs: list of stub files created + test names defined

### Sub-phase B: Coder (replaces Implementer in first iteration)
- Receives the stub files from the Initializer
- Fills in real implementations — one function at a time
- Fills in real test assertions — one test at a time
- Hands off to Tester when all stubs are populated

### When to Use the Split
Use Initializer/Coder when:
- The feature touches 3+ new files
- You want tests defined before implementations (TDD)
- Multiple coders will work in parallel on different stubs

Skip the split (use standard 3-agent loop) when:
- Fixing a bug in existing code
- Adding a small function to an existing file
- The spec is already very concrete

### Modified Flow with Split
```
Initializer → Coder → Tester → [GREEN? → Commit] or [RED? → Fixer → Tester → ...]
```

## Coordination

Uses TaskCreate with blockedBy dependencies for implement -> test -> fix loop.
See `references/loop-flow.md` for iteration limits, commit behavior, and abort conditions.

## Tool Strategy
Call independent tools in parallel (multiple tool calls in one response).
Do NOT read files sequentially when they're independent — batch them.

## Usage

```
/ci:self-heal "add user registration endpoint with email validation"
/ci:self-heal "fix the CSV export bug" --max-iterations 3 --auto-commit
```

## Pipeline Mode

For multi-stage validated builds (implement → test → security → commit), use:
```
/ci:pipeline "add JWT authentication" --auto-commit
```

See `references/pipeline-pattern.md` for the full stage contract and handoff format.
The pipeline uses self-healing CI as its inner loop for the implement stage.
