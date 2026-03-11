"""Pi Status MCP Server - Raw JSON-RPC over stdio.

Monitors Raspberry Pi health over SSH with 4 tools:
  pi_status       - Uptime, memory, disk, temperature
  pi_services     - Running Python/uvicorn processes and listening ports
  pi_deploy_state - Last deployment state from .claude-state.json
  pi_health_check - Quick ping + temperature check

No mcp SDK dependency - implements JSON-RPC 2.0 directly.
"""

import json
import os
import subprocess
import sys
import time

# --- Configuration ---

PI_USER = os.environ.get("PI_USER", "captain")
PI_PASS = os.environ.get("PI_PASS", "")
WIFI_IP = os.environ.get("PI_WIFI_IP", "192.168.2.174")
ETH_IP = os.environ.get("PI_ETH_IP", "192.168.100.10")
IP_CACHE_TTL = 60
SSH_TIMEOUT = 10

# --- IP Discovery ---

_cached_ip = None
_ip_cache_time = 0


def _log(msg):
    """Log to stderr for debugging (visible in MCP server logs)."""
    print(f"[pi-status] {msg}", file=sys.stderr, flush=True)


def find_pi_ip():
    """Find reachable Pi IP. Tries WiFi first, then ethernet. Caches for 60s."""
    global _cached_ip, _ip_cache_time
    now = time.time()
    if _cached_ip and (now - _ip_cache_time) < IP_CACHE_TTL:
        return _cached_ip
    for ip in [WIFI_IP, ETH_IP]:
        try:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "2", ip],
                capture_output=True, timeout=3
            )
            if result.returncode == 0:
                _cached_ip = ip
                _ip_cache_time = now
                _log(f"Pi found at {ip}")
                return ip
        except subprocess.TimeoutExpired:
            continue
        except Exception as e:
            _log(f"Ping error for {ip}: {e}")
            continue
    _log("Pi not reachable on any IP")
    return None


# --- SSH Execution ---


def ssh_run(command):
    """Run a command on the Pi via SSH. Returns dict with output or error."""
    ip = find_pi_ip()
    if not ip:
        return {"error": "Pi not reachable on WiFi or Ethernet"}
    try:
        result = subprocess.run(
            [
                "sshpass", "-p", PI_PASS, "ssh",
                "-o", "StrictHostKeyChecking=no",
                "-o", "ConnectTimeout=5",
                "-o", "UserKnownHostsFile=/dev/null",
                f"{PI_USER}@{ip}", command
            ],
            capture_output=True, text=True, timeout=SSH_TIMEOUT
        )
        if result.returncode != 0 and not result.stdout.strip():
            return {"error": f"Command failed: {result.stderr.strip()}"}
        return {"output": result.stdout.strip(), "ip": ip}
    except subprocess.TimeoutExpired:
        return {"error": f"SSH command timed out ({SSH_TIMEOUT}s)"}
    except FileNotFoundError:
        return {"error": "sshpass not installed. Run: sudo apt install sshpass"}
    except Exception as e:
        return {"error": f"SSH failed: {str(e)}"}


# --- Tool Implementations ---


def tool_pi_status(params):
    """Get Pi health: uptime, memory, disk, temperature."""
    return ssh_run(
        "uptime && echo '---' && "
        "free -h && echo '---' && "
        "df -h / && echo '---' && "
        "vcgencmd measure_temp 2>/dev/null || echo 'temp: N/A'"
    )


def tool_pi_services(params):
    """List running Python/uvicorn processes and listening ports."""
    return ssh_run(
        "echo '=== Python Processes ===' && "
        "pgrep -a python 2>/dev/null || echo 'none' && "
        "echo '=== Uvicorn ===' && "
        "pgrep -a uvicorn 2>/dev/null || echo 'none' && "
        "echo '=== Listening Ports ===' && "
        "ss -tlnp 2>/dev/null | head -20"
    )


def tool_pi_deploy_state(params):
    """Read last deployment state from .claude-state.json."""
    return ssh_run(
        "cat ~/ladesaule-poc/.claude-state.json 2>/dev/null || "
        "echo '{\"error\": \"No deploy state found\"}'"
    )


def tool_pi_health_check(params):
    """Quick health check: ping + temperature."""
    ip = find_pi_ip()
    if not ip:
        return {"status": "unhealthy", "error": "Pi not reachable"}
    result = ssh_run("vcgencmd measure_temp 2>/dev/null || echo 'temp=N/A'")
    if "error" in result:
        return {"status": "unhealthy", "ip": ip, **result}
    temp_str = result.get("output", "")
    return {"status": "healthy", "ip": ip, "temperature": temp_str}


# --- Tool Registry ---

TOOLS = {
    "pi_status": {
        "fn": tool_pi_status,
        "desc": "Get Pi health: uptime, memory, disk, temperature",
        "params": {},
    },
    "pi_services": {
        "fn": tool_pi_services,
        "desc": "List running Python/uvicorn processes and listening ports",
        "params": {},
    },
    "pi_deploy_state": {
        "fn": tool_pi_deploy_state,
        "desc": "Read last deployment state from .claude-state.json",
        "params": {},
    },
    "pi_health_check": {
        "fn": tool_pi_health_check,
        "desc": "Quick health check: ping + temperature",
        "params": {},
    },
}


# --- JSON-RPC Protocol ---


def handle_request(request):
    """Route a JSON-RPC request to the appropriate handler."""
    method = request.get("method", "")
    req_id = request.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "pi-status", "version": "1.0.0"},
            },
        }

    if method == "notifications/initialized":
        return None  # No response for notifications

    if method == "tools/list":
        tools = [
            {
                "name": name,
                "description": info["desc"],
                "inputSchema": {
                    "type": "object",
                    "properties": info["params"],
                },
            }
            for name, info in TOOLS.items()
        ]
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": tools},
        }

    if method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})
        if tool_name not in TOOLS:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Unknown tool: {tool_name}",
                },
            }
        try:
            result = TOOLS[tool_name]["fn"](tool_args)
        except Exception as e:
            _log(f"Tool {tool_name} raised: {e}")
            result = {"error": str(e)}
        content = json.dumps(result, indent=2)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": content}],
            },
        }

    # Unknown method
    if req_id is not None:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Unknown method: {method}",
            },
        }
    return None  # Ignore unknown notifications


def main():
    """Main loop: read JSON-RPC from stdin, write responses to stdout."""
    global PI_PASS
    if not PI_PASS:
        PI_PASS = "captain"
        _log("WARNING: PI_PASS not set in environment, using hardcoded default")
    _log("Server starting")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError as e:
            _log(f"JSON parse error: {e}")
            continue
        _log(f"<-- {request.get('method', '?')}")
        response = handle_request(request)
        if response is not None:
            out = json.dumps(response)
            sys.stdout.write(out + "\n")
            sys.stdout.flush()
            _log(f"--> response for {request.get('method', '?')}")
    _log("Server shutting down (stdin closed)")
