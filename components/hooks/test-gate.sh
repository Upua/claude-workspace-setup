#!/bin/bash
# Hook: Test Gate - Block commits without passing tests
#
# Modes (pass as $1):
#   invalidate  - PostToolUse/Edit: Delete test-pass marker on file edit
#   check-pass  - PostToolUse/Bash: Create marker if test command passed
#   gate        - PreToolUse/Bash: Block git commit if no marker
#
# Marker file: /tmp/claude-test-pass-<project-hash>
# Exit code 2 = BLOCK (only in gate mode)

MODE="${1:-}"
INPUT=$(cat 2>/dev/null || true)

# Derive project identifier from git root or PWD
PROJECT_DIR=$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")
PROJECT_HASH=$(echo "$PROJECT_DIR" | md5sum | cut -c1-8)
MARKER="/tmp/claude-test-pass-${PROJECT_HASH}"

case "$MODE" in
    invalidate)
        # A file was edited - invalidate the test marker
        FILE_PATH=""
        if [ -n "$INPUT" ]; then
            FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""' 2>/dev/null)
        fi
        # Only invalidate for source files, not test output or configs
        if [ -n "$FILE_PATH" ] && [ "$FILE_PATH" != "null" ]; then
            # Skip invalidation for common non-source files
            case "$FILE_PATH" in
                *.log|*.md|*.txt|*.json|*.lock|*.svg|*.png|*.jpg)
                    # Don't invalidate for docs, logs, assets, lockfiles
                    ;;
                *)
                    if [ -f "$MARKER" ]; then
                        /bin/rm -f "$MARKER"
                    fi
                    ;;
            esac
        fi
        ;;

    check-pass)
        # A bash command completed - check if it was a test command that passed
        if [ -z "$INPUT" ]; then
            exit 0
        fi
        CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null)
        EXIT_CODE=$(echo "$INPUT" | jq -r '.tool_exit_code // 1' 2>/dev/null)

        # Check if command is a test command (needed for both pass and fail paths)
        IS_TEST=false
        case "$CMD" in
            *pytest*|*"python -m pytest"*|*"python3 -m pytest"*)
                IS_TEST=true ;;
            *"npm test"*|*"npm run test"*|*"npx jest"*|*"npx vitest"*)
                IS_TEST=true ;;
            *"cargo test"*|*"cargo nextest"*)
                IS_TEST=true ;;
            *"make test"*|*"make check"*)
                IS_TEST=true ;;
            *"go test"*)
                IS_TEST=true ;;
            *"rspec"*|*"bundle exec rspec"*)
                IS_TEST=true ;;
        esac

        # Auto-outcome: if tests FAIL, mark current skill usage
        if [ "$IS_TEST" = true ] && [ "$EXIT_CODE" != "0" ]; then
            if [ -f /tmp/claude_current_skill_usage ]; then
                bash "$HOME/.claude/scripts/skill-tracker.sh" feedback failed "" "Tests failed (auto-detected)" 2>/dev/null || true
            fi
        fi

        # Exit early if command failed (only create pass markers for successes)
        if [ "$EXIT_CODE" != "0" ]; then
            exit 0
        fi

        if [ "$IS_TEST" = true ]; then
            echo "$CMD" > "$MARKER"
            OUTPUT=$(echo "$INPUT" | jq -r '.tool_output // ""' 2>/dev/null | head -50)
            LINE_COUNT=$(echo "$OUTPUT" | wc -l | tr -d ' ')
            echo "Test gate: Tests passed. Commits unlocked for $(basename "$PROJECT_DIR"). (output: ${LINE_COUNT} lines)"

            # Auto-outcome: mark current skill usage as successful
            if [ -f /tmp/claude_current_skill_usage ]; then
                bash "$HOME/.claude/scripts/skill-tracker.sh" feedback success "" "Tests passed (auto-detected)" 2>/dev/null || true
            fi
        fi

        # Auto-outcome: detect successful git commit for code-review tracking
        case "$CMD" in
            *"git commit"*)
                if [ -f /tmp/claude_current_skill_usage ]; then
                    CURRENT_SKILL=$(tail -1 /tmp/claude_current_skill_usage 2>/dev/null || true)
                    if [ "$CURRENT_SKILL" = "code-review" ]; then
                        bash "$HOME/.claude/scripts/skill-tracker.sh" feedback success "" "Commit succeeded after review (auto)" 2>/dev/null || true
                    fi
                fi
                ;;
        esac
        ;;

    gate)
        # Check if a git commit is being attempted
        if [ -z "$INPUT" ]; then
            exit 0
        fi
        CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null)

        # Only gate git commit commands
        if [[ ! "$CMD" =~ git[[:space:]]+commit ]] && [[ ! "$CMD" =~ git\ commit ]]; then
            exit 0
        fi

        # Allow --allow-empty and --amend (these are special cases)
        if [[ "$CMD" =~ --allow-empty ]]; then
            exit 0
        fi

        # SMART CHECK: What files are staged?
        STAGED_FILES=$(git diff --cached --name-only 2>/dev/null || true)

        if [ -z "$STAGED_FILES" ]; then
            # No files staged, let git handle it
            exit 0
        fi

        # Check if ANY Python files are staged
        HAS_PYTHON=$(echo "$STAGED_FILES" | /usr/bin/grep -E '\.py$' || true)

        # Non-code files that don't need tests
        NON_CODE_ONLY=true
        while IFS= read -r file; do
            case "$file" in
                *.md|*.txt|*.json|*.yaml|*.yml|*.css|*.html|*.svg|*.png|*.jpg|*.lock|*.toml)
                    # These don't need tests
                    ;;
                *)
                    NON_CODE_ONLY=false
                    break
                    ;;
            esac
        done <<< "$STAGED_FILES"

        # If only non-code files, skip test requirement
        if [ "$NON_CODE_ONLY" = true ]; then
            echo "Test gate: Only non-code files staged (css/html/md/json). Skipping tests."
            exit 0
        fi

        # Check for test marker first
        if [ -f "$MARKER" ]; then
            echo "Test gate: Commit allowed (tests passed: $(cat "$MARKER" | head -c 80))"
            exit 0
        fi

        # No marker - warn but allow for code changes
        # (Running tests inline from hooks is unreliable)
        if [ -n "$HAS_PYTHON" ]; then
            echo "ERROR: TEST GATE — Python files staged but no test run detected."
            echo "ERROR: Run: pytest && ruff check . before committing."
            exit 0
        fi

        # Other code files - also warn but allow
        echo "ERROR: TEST GATE — Code files staged but tests not verified. Run tests before pushing."
        exit 0
        ;;

    *)
        echo "Usage: test-gate.sh {invalidate|check-pass|gate}" >&2
        exit 1
        ;;
esac

exit 0
