#!/bin/bash
# Hook: Block edits to sensitive files
# Type: PreToolUse hook for Edit/Write/MultiEdit tools
# Exit code 2 = BLOCK the tool from executing

# Read hook input from stdin
INPUT=$(cat)

# Extract the file path being modified
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')

# Skip if no file path
if [ -z "$FILE_PATH" ] || [ "$FILE_PATH" = "null" ]; then
    exit 0
fi

block_edit() {
    echo "BLOCKED: Sensitive file edit prevented"
    echo "Reason: $1"
    echo "File: $FILE_PATH"
    exit 2
}

# Block .env files (any directory)
BASENAME=$(basename "$FILE_PATH")
if [[ "$BASENAME" =~ ^\.env ]] || [[ "$BASENAME" =~ \.env$ ]] || [[ "$FILE_PATH" =~ /\.env($|\.) ]]; then
    block_edit ".env files may contain secrets"
fi

# Block credentials files
if [[ "$(basename "$FILE_PATH")" =~ ^credentials\. ]] || [[ "$(basename "$FILE_PATH")" =~ ^secrets\. ]]; then
    block_edit "Credentials/secrets files"
fi

# Block SSH directory
if [[ "$FILE_PATH" =~ ^(/home/[^/]+|~)/\.ssh/ ]] || [[ "$FILE_PATH" = *"/.ssh/"* ]]; then
    block_edit "SSH configuration and keys"
fi

# Block /etc system configs
if [[ "$FILE_PATH" =~ ^/etc/ ]]; then
    block_edit "/etc/ system configuration files"
fi

# Block /boot
if [[ "$FILE_PATH" =~ ^/boot/ ]]; then
    block_edit "/boot/ bootloader files"
fi

# Block GPG directory
if [[ "$FILE_PATH" = *"/.gnupg/"* ]]; then
    block_edit "GPG keys and configuration"
fi

# Block private key files by extension
if [[ "$FILE_PATH" =~ \.(pem|key|p12|pfx|jks)$ ]]; then
    block_edit "Private key file"
fi

# Allow the edit
exit 0
