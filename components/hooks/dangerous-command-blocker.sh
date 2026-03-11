#!/bin/bash
# Hook: Block Dangerous Commands
# Type: PreToolUse hook for Bash tool
# Exit code 2 = BLOCK the command from executing

# Read hook input from stdin
INPUT=$(cat)

# Extract the command being executed
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

# Check for dangerous patterns using exact string matching and careful regex
block_command() {
    echo "BLOCKED: Dangerous command detected"
    echo "Reason: $1"
    echo "Command was: $COMMAND"
    exit 2
}

# Block rm with recursive+force on absolute paths (catches split flags, path prefixes)
# Patterns: rm -rf /, rm -r -f /, /bin/rm -rf /, command rm -rf /, sudo rm -rf /
if echo "$COMMAND" | grep -qE '(^|&&|\|\||;|sudo|command|/s?bin/)\s*rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|-r\s+-f|-f\s+-r)\s+/' && \
   ! echo "$COMMAND" | grep -qE 'rm\s+.*\s+\./'; then
    block_command "rm with recursive+force on absolute path"
fi

# Block rm -rf on home directory with tilde
if echo "$COMMAND" | grep -qE '(^|&&|\|\||;|sudo|command)\s*rm\s+.*-r.*\s+~'; then
    block_command "rm recursive on home directory"
fi

# Block mkfs (disk formatting)
if echo "$COMMAND" | grep -qE '(^|&&|\|\||;|sudo)\s*mkfs'; then
    block_command "mkfs disk formatting"
fi

# Block dd to devices
if echo "$COMMAND" | grep -qE 'dd\s+.*of=/dev'; then
    block_command "dd to block device"
fi

# Block redirect to devices
if [[ "$COMMAND" =~ \>/dev/sd ]]; then
    block_command "redirect to disk device"
fi

# Block chmod 777 on root
if echo "$COMMAND" | grep -qE 'chmod\s+.*-R.*\s+777\s+/'; then
    block_command "chmod -R 777 on root"
fi

# Block fork bomb (literal string match)
if [[ "$COMMAND" == *":(){ :|:& };:"* ]]; then
    block_command "fork bomb detected"
fi

# Block fdisk, parted, cryptsetup on block devices
if echo "$COMMAND" | grep -qE '(^|&&|\|\||;|sudo)\s*(fdisk|parted|cryptsetup)\s'; then
    block_command "disk partitioning/encryption tool"
fi

# Allow the command
exit 0
