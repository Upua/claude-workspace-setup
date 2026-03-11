"""
Antigravity Bridge - Token Manager
Handles OAuth token loading, refresh, and caching.
Token sources:
1. Bridge token file (bridge-token.txt)
2. SQLite DB (state.vscdb) - protobuf-encoded OAuth token with refresh token
3. OAuth credentials file (~/.gemini/oauth_creds.json)
"""
import base64
import json
import re
import subprocess
import time
import urllib.parse
import urllib.request
from typing import Optional

from config import (
    OAUTH_CREDS_FILE,
    BRIDGE_TOKEN_FILE,
    VSCDB_PATH,
    TOKEN_REFRESH_URL,
    OAUTH_CLIENT_ID,
    OAUTH_CLIENT_SECRET,
    DAILY_API_ENDPOINT,
    LOAD_CODE_ASSIST_PATH,
)


class TokenManager:
    def __init__(self):
        self._access_token: Optional[str] = None
        self._expiry_ms: int = 0
        self._refresh_token: Optional[str] = None
        self._project: Optional[str] = None
        self._csrf_token: Optional[str] = None
        self._load_credentials()

    def _load_credentials(self):
        """Load credentials from available sources."""
        # Priority 1: Extract refresh token from SQLite DB protobuf
        self._load_from_vscdb()

        # Priority 2: Load OAuth creds file as fallback
        if not self._refresh_token and OAUTH_CREDS_FILE.exists():
            with open(OAUTH_CREDS_FILE) as f:
                creds = json.load(f)
                self._access_token = creds.get("access_token")
                self._expiry_ms = creds.get("expiry_date", 0)

        # Discover CSRF token from running language server
        self._discover_ls_credentials()

    def _load_from_vscdb(self):
        """Extract OAuth token and refresh token from Antigravity's SQLite DB."""
        if not VSCDB_PATH.exists():
            return
        try:
            import sqlite3
            db = sqlite3.connect(str(VSCDB_PATH))
            row = db.execute(
                "SELECT value FROM ItemTable WHERE key='antigravityUnifiedStateSync.oauthToken'"
            ).fetchone()
            if not row:
                db.close()
                return

            decoded = base64.b64decode(row[0])
            db.close()

            # Parse protobuf: field 1 = wrapper, field 2 = inner with nested base64
            # The inner base64 decodes to protobuf with:
            #   field 1 = access_token, field 2 = token_type, field 3 = refresh_token
            tokens = self._parse_token_protobuf(decoded)
            if tokens.get("access_token"):
                self._access_token = tokens["access_token"]
            if tokens.get("refresh_token"):
                self._refresh_token = tokens["refresh_token"]
            if tokens.get("expiry"):
                self._expiry_ms = tokens["expiry"] * 1000  # Convert seconds to ms
        except Exception:
            pass

    def _parse_token_protobuf(self, data: bytes) -> dict:
        """Parse the nested protobuf structure from state.vscdb."""
        result = {}
        try:
            # Outer: field 1 (bytes) = wrapper message
            # Inner: field 1 (string) = sentinel key, field 2 (bytes) = token data
            # Token data: field 1 (string) = base64 of inner protobuf
            # Inner protobuf: field 1 = access_token, field 2 = "Bearer", field 3 = refresh_token

            # Simple approach: find all ya29 tokens and refresh tokens in the decoded bytes
            text = data.decode('latin-1')

            # Find base64 chunks and decode them
            b64_chunks = re.findall(r'[A-Za-z0-9+/=_-]{50,}', text)
            for chunk in b64_chunks:
                try:
                    inner = base64.b64decode(chunk + '==')
                    inner_text = inner.decode('latin-1')

                    # Extract ya29 access token
                    token_match = re.search(r'ya29\.[A-Za-z0-9_.-]+', inner_text)
                    if token_match:
                        result["access_token"] = token_match.group(0)

                    # Extract refresh token (1// pattern)
                    refresh_match = re.search(r'1//[A-Za-z0-9_+/=-]+', inner_text)
                    if refresh_match:
                        result["refresh_token"] = refresh_match.group(0)
                except Exception:
                    continue

            # Extract expiry timestamp from protobuf varints
            # Look for field 4 (varint) which contains the expiry
            ya29_pos = text.find('ya29.')
            if ya29_pos > 0:
                # Search for timestamp-like varints after the tokens
                for m in re.finditer(rb'\x08([\x80-\xff]*[\x00-\x7f])', data[ya29_pos:]):
                    val = self._decode_varint(m.group(1))
                    if 1700000000 < val < 1900000000:  # Reasonable epoch range
                        result["expiry"] = val
                        break

        except Exception:
            pass
        return result

    @staticmethod
    def _decode_varint(data: bytes) -> int:
        """Decode a protobuf varint from bytes."""
        val = 0
        shift = 0
        for b in data:
            val |= (b & 0x7F) << shift
            shift += 7
            if not (b & 0x80):
                break
        return val

    def _discover_ls_credentials(self):
        """Extract CSRF token from running language server process."""
        try:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.split('\n'):
                if 'language_server' in line and '--csrf_token' in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == '--csrf_token' and i + 1 < len(parts):
                            self._csrf_token = parts[i + 1]
                    break
        except Exception:
            pass

    def get_access_token(self) -> Optional[str]:
        """Get a valid access token, refreshing if needed."""
        # Priority 1: Direct token file (freshest, written externally)
        if BRIDGE_TOKEN_FILE.exists():
            try:
                token = BRIDGE_TOKEN_FILE.read_text().strip()
                if token and len(token) > 20:
                    # Check if it's still valid
                    now_ms = int(time.time() * 1000)
                    if now_ms < self._expiry_ms - 60000:
                        return token
                    # Token might be expired, but try it as last resort
                    self._access_token = token
            except Exception:
                pass

        # Priority 2: Check if cached token is still valid
        now_ms = int(time.time() * 1000)
        if self._access_token and now_ms < self._expiry_ms - 60000:
            return self._access_token

        # Priority 3: Refresh using refresh token from SQLite DB
        if self._refresh_token:
            refreshed = self._refresh_oauth_token()
            if refreshed:
                return self._access_token

        # Priority 4: Re-read from SQLite DB (LS might have updated it)
        self._load_from_vscdb()
        if self._access_token:
            return self._access_token

        return self._access_token  # Return whatever we have

    def get_project(self) -> Optional[str]:
        """Get the cloudaicompanionProject for API calls."""
        if self._project:
            return self._project

        # Discover project via loadCodeAssist API
        token = self.get_access_token()
        if not token:
            return None

        try:
            url = f"{DAILY_API_ENDPOINT}{LOAD_CODE_ASSIST_PATH}"
            data = json.dumps({}).encode()
            req = urllib.request.Request(url, data=data, method="POST")
            req.add_header("Authorization", f"Bearer {token}")
            req.add_header("Content-Type", "application/json")

            resp = urllib.request.urlopen(req, timeout=15)
            result = json.loads(resp.read())
            self._project = result.get("cloudaicompanionProject", "")
            return self._project
        except Exception:
            return None

    def _refresh_oauth_token(self) -> bool:
        """Refresh the OAuth access token using the refresh token."""
        if not self._refresh_token:
            return False

        try:
            data = urllib.parse.urlencode({
                "client_id": OAUTH_CLIENT_ID,
                "client_secret": OAUTH_CLIENT_SECRET,
                "refresh_token": self._refresh_token,
                "grant_type": "refresh_token"
            }).encode()

            req = urllib.request.Request(TOKEN_REFRESH_URL, data=data, method="POST")
            req.add_header("Content-Type", "application/x-www-form-urlencoded")

            resp = urllib.request.urlopen(req, timeout=10)
            result = json.loads(resp.read())

            self._access_token = result["access_token"]
            self._expiry_ms = int(time.time() * 1000) + (result["expires_in"] * 1000)

            # Write fresh token to bridge file
            try:
                BRIDGE_TOKEN_FILE.write_text(self._access_token)
            except Exception:
                pass

            return True
        except Exception:
            return False

    def get_csrf_token(self) -> Optional[str]:
        """Get the CSRF token for language server gRPC calls."""
        if not self._csrf_token:
            self._discover_ls_credentials()
        return self._csrf_token

    def status(self) -> dict:
        """Return token status info."""
        now_ms = int(time.time() * 1000)
        token = self.get_access_token()
        return {
            "has_token": bool(token),
            "token_expired": now_ms > self._expiry_ms if self._expiry_ms else True,
            "token_source": self._determine_token_source(),
            "has_refresh_token": bool(self._refresh_token),
            "has_csrf_token": bool(self._csrf_token),
            "project": self._project or "(not yet discovered)",
            "bridge_token_file_exists": BRIDGE_TOKEN_FILE.exists(),
        }

    def _determine_token_source(self) -> str:
        if self._refresh_token:
            return "vscdb-refresh"
        if BRIDGE_TOKEN_FILE.exists():
            token = BRIDGE_TOKEN_FILE.read_text().strip()
            if token and len(token) > 20:
                return "bridge-token-file"
        return "none"
