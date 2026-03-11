#!/bin/bash
# Hook: Save state before context compaction
# Type: PreCompact hook (fires before Claude compacts context)
# Saves key session state so it survives compaction
#
# Output: ~/.claude/pre-compact-state.md

set -euo pipefail

STATE_FILE="$HOME/.claude/pre-compact-state.md"
MEMORY_FILE="$HOME/.claude/memory.json"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M)

{
    echo "# Pre-Compaction State"
    echo "Saved: $TIMESTAMP"
    echo ""

    # Current working directory
    echo "## Working Directory"
    echo "\`$PWD\`"
    echo ""

    # Recent file edits from memory.json (last 5)
    if [ -f "$MEMORY_FILE" ] && command -v jq &>/dev/null; then
        EDITS=$(jq -r '
            [.memories[] | select(.category == "edit")] | .[-5:][] |
            .content | gsub("File modified: "; "") | gsub(" \\(success=true\\)"; "")
        ' "$MEMORY_FILE" 2>/dev/null | head -5)

        if [ -n "$EDITS" ]; then
            echo "## Recent File Edits"
            echo "$EDITS" | while read -r line; do
                [ -n "$line" ] && echo "- \`$line\`"
            done
            echo ""
        fi

        # Recent commands from memory.json (last 5)
        COMMANDS=$(jq -r '
            [.memories[] | select(.category == "command")] | .[-5:][] |
            .content | .[0:120]
        ' "$MEMORY_FILE" 2>/dev/null | head -5)

        if [ -n "$COMMANDS" ]; then
            echo "## Recent Commands"
            echo "$COMMANDS" | while read -r line; do
                [ -n "$line" ] && echo "- $line"
            done
            echo ""
        fi

        # Any feedback entries
        FEEDBACK=$(jq -r '
            [.memories[] | select(.category == "feedback")] | .[-3:][] |
            .content
        ' "$MEMORY_FILE" 2>/dev/null | head -3)

        if [ -n "$FEEDBACK" ]; then
            echo "## Recent Feedback"
            echo "$FEEDBACK" | while read -r line; do
                [ -n "$line" ] && echo "- $line"
            done
            echo ""
        fi
    fi

    # Git status if in a repo
    if git rev-parse --is-inside-work-tree &>/dev/null; then
        BRANCH=$(git branch --show-current 2>/dev/null)
        DIRTY=$(git status --porcelain 2>/dev/null | wc -l)
        echo "## Git State"
        echo "- Branch: \`$BRANCH\`"
        echo "- Uncommitted changes: $DIRTY files"
        echo ""
    fi

    echo "---"
    echo "*This state was saved automatically before context compaction.*"
    echo "*Use this to re-orient after compaction.*"

} > "$STATE_FILE" 2>/dev/null

echo "Pre-compact state saved to $STATE_FILE"
exit 0
