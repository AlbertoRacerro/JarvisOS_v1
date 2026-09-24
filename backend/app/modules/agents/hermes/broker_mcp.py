"""One read-only MCP stdio bridge to the Jarvis worker relay (stdlib only)."""
from __future__ import annotations

import json
import os
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

_TOOL = {
    "name": "jarvis_context_preview",
    "description": "Preview exact Jarvis context refs using a live Jarvis capability grant.",
    "inputSchema": {
        "type": "object", "properties": {
            "grant_id": {"type": "string"},
            "request": {"type": "object"},
        }, "required": ["grant_id", "request"], "additionalProperties": False,
    },
}


class _DenyRedirects(HTTPRedirectHandler):
    def redirect_request(self, *_args: Any, **_kwargs: Any) -> None:
        return None


def _reply(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    request_id = message.get("id")
    if request_id is None:
        return None
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": request_id, "result": {
            "protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
            "serverInfo": {"name": "jarvis", "version": "1"}}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": [_TOOL]}}
    if method == "tools/call":
        params = message.get("params") or {}
        if params.get("name") != _TOOL["name"]:
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "unknown tool"}}
        encoded = json.dumps(params.get("arguments") or {}).encode()
        broker_url = os.environ["JARVIS_HERMES_BROKER_URL"]
        parsed = urlsplit(broker_url)
        if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or parsed.path != "/v1/jarvis/tool":
            return {"jsonrpc": "2.0", "id": request_id,
                    "error": {"code": -32603, "message": "invalid Jarvis broker endpoint"}}
        request = Request(broker_url, data=encoded,
                          headers={"Authorization": f"Bearer {os.environ['JARVIS_HERMES_BROKER_TOKEN']}",
                                   "Content-Type": "application/json"})
        try:
            opener = build_opener(ProxyHandler({}), _DenyRedirects())
            with opener.open(request, timeout=120) as response:
                result = json.load(response)
            content = json.dumps(result, separators=(",", ":"))
            return {"jsonrpc": "2.0", "id": request_id, "result": {
                "content": [{"type": "text", "text": content}],
                "isError": result.get("status") != "succeeded"}}
        except (HTTPError, URLError, ValueError):
            return {"jsonrpc": "2.0", "id": request_id, "result": {
                "content": [{"type": "text", "text": "Jarvis capability unavailable"}], "isError": True}}
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "unknown method"}}


def main() -> None:
    for line in sys.stdin:
        try:
            request = json.loads(line)
            response = _reply(request)
            if response is not None:
                sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
                sys.stdout.flush()
        except (ValueError, KeyError):
            pass


if __name__ == "__main__":
    main()
