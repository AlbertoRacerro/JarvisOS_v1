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
_RETRIEVAL_TOOL = {
    "name": "jarvis_retrieval_query",
    "description": "Find bounded, current Second Brain evidence within the live grant scope.",
    "inputSchema": {
        "type": "object", "properties": {
            "grant_id": {"type": "string"},
            "query": {"type": "string", "maxLength": 2000},
            "source_scope": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 32},
            "limit": {"type": "integer", "minimum": 1, "maximum": 8},
            "token_budget": {"type": "integer", "minimum": 1, "maximum": 1024},
        }, "required": ["grant_id", "query", "source_scope"], "additionalProperties": False,
    },
}
_DECISION_TOOL = {
    "name": "jarvis_decide",
    "description": "Request bounded, non-authoritative Jarvis decision advice.",
    "inputSchema": {
        "type": "object", "properties": {
            "grant_id": {"type": "string", "minLength": 1, "maxLength": 128},
            "kind": {"type": "string", "enum": ["route_class", "retry_or_stop", "escalate", "model_select"]},
            "request": {"type": "object"},
        }, "required": ["grant_id", "kind", "request"], "additionalProperties": False,
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
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": [_TOOL, _RETRIEVAL_TOOL, _DECISION_TOOL]}}
    if method == "tools/call":
        params = message.get("params") or {}
        if params.get("name") not in {_TOOL["name"], _RETRIEVAL_TOOL["name"], _DECISION_TOOL["name"]}:
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "unknown tool"}}
        body = params.get("arguments") or {}
        if params.get("name") == _RETRIEVAL_TOOL["name"] and isinstance(body, dict):
            body = {**body, "tool_name": _RETRIEVAL_TOOL["name"]}
        if params.get("name") == _DECISION_TOOL["name"] and isinstance(body, dict):
            body = {**body, "tool_name": _DECISION_TOOL["name"]}
        encoded = json.dumps(body).encode()
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
