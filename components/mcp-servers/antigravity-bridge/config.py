"""
Antigravity Bridge - Configuration

OAuth credentials are extracted from the local Antigravity installation
or can be set via environment variables.
"""
import json
import os
from pathlib import Path

# Paths
GEMINI_DIR = Path.home() / ".gemini"
OAUTH_CREDS_FILE = GEMINI_DIR / "oauth_creds.json"
BRIDGE_DIR = Path(__file__).parent
BRIDGE_CREDS_FILE = BRIDGE_DIR / ".credentials.json"
BRIDGE_TOKEN_FILE = BRIDGE_DIR / "bridge-token.txt"
VSCDB_PATH = Path.home() / ".config" / "Antigravity" / "User" / "globalStorage" / "state.vscdb"
LOG_FILE = BRIDGE_DIR / "bridge.log"

# Cloud API
CLOUD_API_ENDPOINT = "https://cloudcode-pa.googleapis.com"
DAILY_API_ENDPOINT = "https://daily-cloudcode-pa.googleapis.com"
TOKEN_REFRESH_URL = "https://oauth2.googleapis.com/token"
LOAD_CODE_ASSIST_PATH = "/v1internal:loadCodeAssist"
GENERATE_CONTENT_PATH = "/v1internal:generateContent"


def _detect_oauth_credentials() -> tuple[str, str]:
    """Auto-detect OAuth credentials from Antigravity installation or env vars."""
    # Priority 1: Environment variables
    client_id = os.environ.get("ANTIGRAVITY_CLIENT_ID", "")
    client_secret = os.environ.get("ANTIGRAVITY_CLIENT_SECRET", "")
    if client_id and client_secret:
        return client_id, client_secret

    # Priority 2: Antigravity extension's oauthClient.js (extract from installed app)
    ag_locations = [
        Path.home() / ".vscode" / "extensions",
        Path.home() / ".vscode-insiders" / "extensions",
        Path.home() / ".cursor" / "extensions",
    ]
    for ext_dir in ag_locations:
        if not ext_dir.exists():
            continue
        for d in ext_dir.iterdir():
            if "antigravity" in d.name.lower():
                oauth_file = d / "dist" / "oauthClient.js"
                if oauth_file.exists():
                    content = oauth_file.read_text()
                    # Extract client ID and secret from JS source
                    import re
                    id_match = re.search(r'"(\d+[^"]*\.apps\.googleusercontent\.com)"', content)
                    secret_match = re.search(r'"(GOCSPX-[^"]+)"', content)
                    if id_match and secret_match:
                        return id_match.group(1), secret_match.group(1)

    # Priority 3: Existing credentials file
    if BRIDGE_CREDS_FILE.exists():
        try:
            creds = json.loads(BRIDGE_CREDS_FILE.read_text())
            return creds.get("client_id", ""), creds.get("client_secret", "")
        except (json.JSONDecodeError, KeyError):
            pass

    return "", ""


OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET = _detect_oauth_credentials()

# Model mappings (friendly name -> API model ID)
MODELS = {
    "gemini-3.1-pro": "gemini-3.1-pro-preview",
    "gemini-3-pro": "gemini-3-pro-preview",
    "gemini-3-flash": "gemini-3-flash-preview",
    "gemini-2.5-pro": "gemini-2.5-pro",
    "gemini-2.5-flash": "gemini-2.5-flash",
    "gemini-2.0-flash": "gemini-2.0-flash",
}
DEFAULT_MODEL = "gemini-2.0-flash"

# Language Server (local gRPC proxy)
LS_GRPC_PORT = 44417
LS_CSRF_TOKEN = None  # Set dynamically from process args

# Timeouts
API_TIMEOUT = 60
GRPC_TIMEOUT = 30
