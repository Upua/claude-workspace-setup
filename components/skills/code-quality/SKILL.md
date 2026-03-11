---
name: code-quality
description: Code review, refactoring, testing, and dependency management. Use for PRs, code smells, test coverage, and dependency audits.
---

# Code Quality

## Code Review
- Check: security (injection, auth, secrets), performance (N+1, unbounded), error handling, naming, complexity
- Severity levels: CRITICAL (security/data loss), HIGH (bugs/perf), MEDIUM (maintainability), LOW (style)
- Format: `[SEVERITY] file:line — description + fix suggestion`

## Refactoring
- Identify code smells: long methods (>30 lines), deep nesting (>3 levels), duplicate code, feature envy, god classes
- Patterns: extract method/variable, replace conditional with polymorphism, introduce parameter object
- Safety: run tests before AND after. Refactor in small, committed steps.

## Testing
- Naming: `test_<what>_<condition>_<expected>` (Python) / `describe/it` (JS)
- Coverage targets: 80% line, 90% branch for critical paths
- Edge cases: empty inputs, nulls, boundaries, unicode, concurrent access
- Test pyramid: many unit, fewer integration, minimal e2e
- Mocking: mock at boundaries (HTTP, DB, filesystem), never mock the SUT

## Dependencies
- Audit: `pip-audit` / `npm audit` / `cargo audit` for known vulnerabilities
- Update strategy: patch versions freely, minor with testing, major with migration plan
- License: check compatibility (MIT/Apache OK, GPL viral, AGPL server-side)
- Lockfiles: always commit them, review diffs on update
