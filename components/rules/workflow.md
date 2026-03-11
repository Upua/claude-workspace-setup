# Workflow Rules

## Debugging
- Before investigating any bug: call `cortex_find_solution` with the error text. The daemon caches problem→fix pairs across projects.
- After successfully fixing a bug: call `cortex_record_solution` with the problem description, solution, and relevant tags so the fix is cached for future sessions.

## Session Orientation
- At session start, `cortex_project_status` is called automatically via hooks. Use the briefing to understand what changed since last session.
- If cortex reports recent errors or solutions for the current project, address them proactively.

## Commit Flow
- Test gate and security gate must pass before committing code files.
- Gates are invalidated automatically when source files are edited — re-run tests after changes.
- Non-code files (md, json, css, html) skip gate requirements.
