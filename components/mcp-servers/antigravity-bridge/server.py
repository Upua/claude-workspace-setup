"""
Antigravity Bridge - MCP Server
Exposes Antigravity's model access as MCP tools for Claude Code.
"""
import json
import sys
import traceback
from datetime import datetime

from config import LOG_FILE, MODELS, DEFAULT_MODEL
from token_manager import TokenManager
from api_client import AntigravityAPIClient

JSONRPC_VERSION = "2.0"

token_manager = TokenManager()
api_client = AntigravityAPIClient(token_manager)

TOOLS = [
    {
        "name": "ag_generate",
        "description": """Send a prompt to an Antigravity model and get a response.
Available models: gemini-2.0-flash (default, fastest), gemini-2.5-flash, gemini-2.5-pro,
gemini-3-flash, gemini-3-pro, gemini-3.1-pro (most capable).
Use this to offload tasks to Gemini and save Claude API tokens.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The prompt to send to the model",
                },
                "model": {
                    "type": "string",
                    "description": f"Model to use. Default: {DEFAULT_MODEL}",
                    "enum": list(MODELS.keys()),
                    "default": DEFAULT_MODEL,
                },
                "system": {
                    "type": "string",
                    "description": "Optional system instruction",
                    "default": "",
                },
                "temperature": {
                    "type": "number",
                    "description": "Temperature (0.0-2.0). Default: 0.7",
                    "default": 0.7,
                },
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "ag_models",
        "description": "List all available models in Antigravity with their IDs.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "ag_status",
        "description": "Check Antigravity bridge health: API connectivity, token status, language server.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]


def log(msg: str):
    """Append to bridge log."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass


def handle_tool_call(name: str, arguments: dict) -> dict:
    """Route tool calls to handlers."""
    if name == "ag_generate":
        prompt = arguments.get("prompt", "")
        model = arguments.get("model", DEFAULT_MODEL)
        system = arguments.get("system", "")
        temperature = arguments.get("temperature", 0.7)

        log(f"ag_generate: model={model}, prompt_len={len(prompt)}")
        result = api_client.generate(prompt, model, system, temperature)
        log(f"ag_generate: result={'error' if 'error' in result else 'ok'}")
        return result

    elif name == "ag_models":
        models = api_client.list_models()
        return {"models": models, "default": DEFAULT_MODEL}

    elif name == "ag_status":
        status = api_client.status()
        # Also check if language server is running
        import subprocess
        try:
            ps = subprocess.run(["pgrep", "-f", "language_server"], capture_output=True, timeout=5)
            status["language_server_running"] = ps.returncode == 0
        except Exception:
            status["language_server_running"] = False
        return status

    else:
        return {"error": f"Unknown tool: {name}"}


def send_response(response: dict):
    """Write JSON-RPC response to stdout."""
    msg = json.dumps(response)
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def process_message(message: dict):
    """Process a JSON-RPC message."""
    method = message.get("method", "")
    msg_id = message.get("id")
    params = message.get("params", {})

    if method == "initialize":
        send_response({
            "jsonrpc": JSONRPC_VERSION,
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "antigravity-bridge",
                    "version": "0.1.0",
                },
            },
        })

    elif method == "notifications/initialized":
        pass  # No response needed

    elif method == "tools/list":
        send_response({
            "jsonrpc": JSONRPC_VERSION,
            "id": msg_id,
            "result": {"tools": TOOLS},
        })

    elif method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        try:
            result = handle_tool_call(tool_name, arguments)
            text = json.dumps(result, indent=2, ensure_ascii=False)
            send_response({
                "jsonrpc": JSONRPC_VERSION,
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": text}],
                },
            })
        except Exception as e:
            log(f"ERROR: {tool_name}: {traceback.format_exc()}")
            send_response({
                "jsonrpc": JSONRPC_VERSION,
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps({"error": str(e)})}],
                    "isError": True,
                },
            })

    elif method == "ping":
        send_response({
            "jsonrpc": JSONRPC_VERSION,
            "id": msg_id,
            "result": {},
        })

    else:
        if msg_id is not None:
            send_response({
                "jsonrpc": JSONRPC_VERSION,
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            })


def main():
    """Main loop: read JSON-RPC messages from stdin, process, respond on stdout."""
    log("Antigravity Bridge starting...")
    log(f"Token status: {token_manager.status()}")

    buffer = ""
    for line in sys.stdin:
        buffer += line
        try:
            message = json.loads(buffer)
            buffer = ""
            process_message(message)
        except json.JSONDecodeError:
            continue
        except Exception:
            log(f"FATAL: {traceback.format_exc()}")
            buffer = ""


if __name__ == "__main__":
    main()
