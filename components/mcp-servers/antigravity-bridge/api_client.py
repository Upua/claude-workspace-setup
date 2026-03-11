"""
Antigravity Bridge - API Client
Handles communication with Antigravity's Cloud API.
Uses the v1internal:generateContent endpoint with project-based routing.
"""
import json
import urllib.request
import urllib.error

from config import DAILY_API_ENDPOINT, GENERATE_CONTENT_PATH, MODELS, DEFAULT_MODEL, API_TIMEOUT
from token_manager import TokenManager


class AntigravityAPIClient:
    def __init__(self, token_manager: TokenManager):
        self.token_manager = token_manager
        self.api_endpoint = DAILY_API_ENDPOINT

    def generate(
        self,
        prompt: str,
        model: str = DEFAULT_MODEL,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> dict:
        """Send a prompt and get a response from an Antigravity model."""
        token = self.token_manager.get_access_token()
        if not token:
            return {"error": "No valid access token. Token refresh may have failed."}

        project = self.token_manager.get_project()
        if not project:
            return {"error": "Could not discover cloudaicompanionProject. Is Antigravity running?"}

        # Resolve model name
        model_id = MODELS.get(model, model)

        # Build request body
        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        request_body = {
            "model": model_id,
            "project": project,
            "request": {
                "contents": contents,
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                },
            },
        }

        if system:
            request_body["request"]["systemInstruction"] = {
                "parts": [{"text": system}]
            }

        # Make API call
        url = f"{self.api_endpoint}{GENERATE_CONTENT_PATH}"
        data = json.dumps(request_body).encode()

        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Content-Type", "application/json")

        try:
            resp = urllib.request.urlopen(req, timeout=API_TIMEOUT)
            result = json.loads(resp.read())
            return self._parse_response(result)
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            error_info = {"error": f"API error {e.code}", "details": body[:500]}

            # If 401, try refreshing token and retrying once
            if e.code == 401:
                self.token_manager._refresh_oauth_token()
                new_token = self.token_manager.get_access_token()
                if new_token and new_token != token:
                    req2 = urllib.request.Request(url, data=data, method="POST")
                    req2.add_header("Authorization", f"Bearer {new_token}")
                    req2.add_header("Content-Type", "application/json")
                    try:
                        resp2 = urllib.request.urlopen(req2, timeout=API_TIMEOUT)
                        result2 = json.loads(resp2.read())
                        return self._parse_response(result2)
                    except Exception:
                        pass

            return error_info
        except Exception as e:
            return {"error": str(e)}

    def list_models(self) -> list:
        """List available models."""
        return [
            {"id": model_id, "name": name}
            for name, model_id in MODELS.items()
        ]

    def _parse_response(self, result: dict) -> dict:
        """Parse Cloud API response into a clean format."""
        try:
            # Response is wrapped in a "response" field
            response = result.get("response", result)
            candidates = response.get("candidates", [])
            if not candidates:
                return {"error": "No candidates in response", "raw": str(result)[:500]}

            candidate = candidates[0]
            content = candidate.get("content", {})
            parts = content.get("parts", [])
            text_parts = [p.get("text", "") for p in parts if "text" in p]
            text = "\n".join(text_parts)

            usage = response.get("usageMetadata", {})

            return {
                "text": text,
                "model": response.get("modelVersion", result.get("model", "unknown")),
                "usage": {
                    "prompt_tokens": usage.get("promptTokenCount", 0),
                    "completion_tokens": usage.get("candidatesTokenCount", 0),
                    "total_tokens": usage.get("totalTokenCount", 0),
                },
                "finish_reason": candidate.get("finishReason", "unknown"),
            }
        except Exception as e:
            return {"error": f"Failed to parse response: {e}", "raw": str(result)[:500]}

    def status(self) -> dict:
        """Check API connectivity and auth status."""
        token_status = self.token_manager.status()
        return {
            "api_endpoint": self.api_endpoint,
            "token": token_status,
            "models_available": len(MODELS),
        }
