#!/bin/bash
# Hook: Quality Gate - Run security checks before commits
#
# Modes (pass as $1):
#   check-security - PostToolUse/Bash: Mark security scan as passed
#   scan           - PreToolUse/Bash: Run quick security scan before commit
#   gate           - PreToolUse/Bash: Block commit without security marker (or run inline scan)
#
# Works alongside test-gate.sh to ensure both tests AND security pass before commits.
#
# Marker file: /tmp/claude-security-pass-<project-hash>
# Exit code 2 = BLOCK

MODE="${1:-}"
INPUT=$(cat 2>/dev/null || true)

# Derive project identifier from git root or PWD
PROJECT_DIR=$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")
PROJECT_HASH=$(echo "$PROJECT_DIR" | md5sum | cut -c1-8)
SECURITY_MARKER="/tmp/claude-security-pass-${PROJECT_HASH}"

# Security patterns to scan for (basic checks that don't require external tools)
check_security_patterns() {
    local dir="$1"
    local issues=0

    # Check for hardcoded secrets in common patterns
    if /usr/bin/grep -rE "(password|secret|api[_-]?key|token|credential)\s*=\s*['\"][^'\"]+['\"]" \
        --include="*.py" --include="*.js" --include="*.ts" --include="*.go" \
        --include="*.rs" --include="*.rb" --include="*.sh" \
        "$dir" 2>/dev/null | grep -v "test" | grep -v "example" | head -5 | grep -q .; then
        echo "SECURITY: Potential hardcoded secrets found"
        issues=$((issues + 1))
    fi

    # Check for dangerous functions in Python
    if find "$dir" -maxdepth 2 -name "*.py" -type f 2>/dev/null | head -1 | grep -q .; then
        if grep -rE "(eval\(|exec\(|__import__|yaml\.load\(|subprocess\.call.*shell=True)" \
            --include="*.py" "$dir" 2>/dev/null | grep -v "#.*eval" | head -3 | grep -q .; then
            echo "SECURITY: Dangerous Python functions found (eval/exec/yaml)"
            issues=$((issues + 1))
        fi
    fi

    # Check for SQL injection patterns
    if /usr/bin/grep -rE "(execute|query).*['\"].*(%s|\$|{|\+.*select|\.format)" \
        --include="*.py" --include="*.js" --include="*.ts" --include="*.go" \
        "$dir" 2>/dev/null | grep -v "test" | head -3 | grep -q .; then
        echo "SECURITY: Potential SQL injection patterns found"
        issues=$((issues + 1))
    fi

    # Check for .env files that might be committed
    if git -C "$dir" ls-files --cached 2>/dev/null | grep -E "\.env$|\.env\." | grep -v "\.env\.example" | grep -q .; then
        echo "SECURITY: .env files staged for commit"
        issues=$((issues + 1))
    fi

    # Check for private keys
    if git -C "$dir" ls-files --cached 2>/dev/null | grep -E "\.(pem|key|p12|pfx)$" | grep -q .; then
        echo "SECURITY: Private key files staged for commit"
        issues=$((issues + 1))
    fi

    return $issues
}

case "$MODE" in
    check-security)
        # A bash command completed - check if it was a security scan that passed
        if [ -z "$INPUT" ]; then
            exit 0
        fi
        CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null)
        EXIT_CODE=$(echo "$INPUT" | jq -r '.tool_exit_code // 1' 2>/dev/null)

        # Only mark as passed if exit code is 0
        if [ "$EXIT_CODE" != "0" ]; then
            exit 0
        fi

        # Check if command is a security scan
        IS_SECURITY=false
        case "$CMD" in
            *bandit*|*safety*|*snyk*|*trivy*|*semgrep*|*"npm audit"*|*"yarn audit"*)
                IS_SECURITY=true ;;
            *"cargo audit"*|*"cargo deny"*)
                IS_SECURITY=true ;;
            *"gosec"*|*"staticcheck"*)
                IS_SECURITY=true ;;
            */gate:security*|*/review:security*)
                IS_SECURITY=true ;;
        esac

        if [ "$IS_SECURITY" = true ]; then
            echo "$CMD" > "$SECURITY_MARKER"
            echo "Quality gate: Security scan passed. Commits allowed for $(basename "$PROJECT_DIR")."

            # Auto-outcome: mark current skill usage as success
            if [ -f /tmp/claude_current_skill_usage ]; then
                CURRENT_SKILL=$(tail -1 /tmp/claude_current_skill_usage 2>/dev/null || true)
                if [ "$CURRENT_SKILL" = "security" ]; then
                    bash "$HOME/.claude/scripts/skill-tracker.sh" feedback success "" "Security scan passed (auto-detected)" 2>/dev/null || true
                fi
            fi
        fi
        ;;

    scan)
        # Run an inline security scan
        ISSUES=$(check_security_patterns "$PROJECT_DIR" 2>&1)
        ISSUE_COUNT=$?

        if [ $ISSUE_COUNT -gt 0 ]; then
            echo "SECURITY SCAN RESULTS"
            echo "====================="
            echo "$ISSUES"
            echo ""
            echo "Found $ISSUE_COUNT potential security issues."
            echo "Review and fix before committing, or run a full security scan:"
            echo "  /gate:security or /review:security"

            exit 2
        else
            echo "Quick security scan: No obvious issues found."
            echo "OK" > "$SECURITY_MARKER"
        fi
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

        # Allow --allow-empty (special case)
        if [[ "$CMD" =~ --allow-empty ]]; then
            exit 0
        fi

        # SMART CHECK: What files are staged?
        STAGED_FILES=$(git diff --cached --name-only 2>/dev/null || true)

        if [ -z "$STAGED_FILES" ]; then
            exit 0
        fi

        # Check if any files need security scanning
        NEEDS_SECURITY_SCAN=false
        while IFS= read -r file; do
            case "$file" in
                *.py|*.js|*.ts|*.go|*.rs|*.rb|*.sh|*.php)
                    NEEDS_SECURITY_SCAN=true
                    break
                    ;;
            esac
        done <<< "$STAGED_FILES"

        # If only non-code files (css/html/md/json/etc), skip security scan
        if [ "$NEEDS_SECURITY_SCAN" = false ]; then
            echo "Quality gate: Only non-code files staged. Skipping security scan."
            exit 0
        fi

        # Check for security marker
        if [ -f "$SECURITY_MARKER" ]; then
            echo "Quality gate: Security check passed ($(cat "$SECURITY_MARKER" | head -c 60))"
            exit 0
        fi

        # No marker - warn but allow (inline scanning is unreliable in hooks)
        echo "Quality gate: Code files staged but security not verified."
        echo "   Recommend: Run '/gate:security' before pushing."
        echo "   Allowing commit (run security scan to remove this warning)."
        exit 0
        ;;

    invalidate)
        # Source files changed - invalidate security marker
        FILE_PATH=""
        if [ -n "$INPUT" ]; then
            FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""' 2>/dev/null)
        fi

        # Only invalidate for source files
        if [ -n "$FILE_PATH" ] && [ "$FILE_PATH" != "null" ]; then
            case "$FILE_PATH" in
                *.log|*.md|*.txt|*.json|*.lock|*.svg|*.png|*.jpg|*.css)
                    # Don't invalidate for docs, logs, assets, styles
                    ;;
                *)
                    if [ -f "$SECURITY_MARKER" ]; then
                        /bin/rm -f "$SECURITY_MARKER"
                    fi
                    ;;
            esac
        fi
        ;;

    *)
        echo "Usage: quality-gate.sh {check-security|scan|gate|invalidate}" >&2
        exit 1
        ;;
esac

exit 0
