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


_QUANTITY = {"type": "object", "properties": {"value": {"type": "number"}, "unit": {"type": "string"}},
             "required": ["value", "unit"], "additionalProperties": False}
_PROCESS_READ_TOOL = {
    "name": "jarvis_process_read",
    "description": "Read the current Jarvis process flowsheet draft: tags, typed parameters with units, "
                   "findings and whether DWSIM results are current or stale.",
    "inputSchema": {
        "type": "object", "properties": {
            "grant_id": {"type": "string", "minLength": 1, "maxLength": 128},
        }, "required": ["grant_id"], "additionalProperties": False,
    },
}
_PROCESS_ACT_TOOL = {
    "name": "jarvis_process_act",
    "description": "Request supported typed Process changes. Use exact tags and base revision from jarvis_process_read; unsupported reactions/thermo stay in the editor.",
    "inputSchema": {"type": "object", "properties": {
        "grant_id": {"type": "string", "maxLength": 128},
        "base_revision": {"type": "string", "maxLength": 64},
        "actions": {"type": "array", "minItems": 1, "maxItems": 8, "items": {"oneOf": [
            {"type": "object", "properties": {"op": {"const": "set_value"}, "target": {"type": "string"},
             "property": {"type": "string"}, "value": {"oneOf": [_QUANTITY, {"type": "string"},
             {"type": "object", "additionalProperties": {"type": "number"}}]}},
             "required": ["op", "target", "property", "value"], "additionalProperties": False},
            {"type": "object", "properties": {"op": {"const": "add_unit"}, "type": {"type": "string"},
             "tag": {"type": "string"}, "near": {"type": "string"}}, "required": ["op", "type"],
             "additionalProperties": False},
            {"type": "object", "properties": {"op": {"const": "insert_unit_after"}, "type": {"type": "string"},
             "after": {"type": "string"}, "tag": {"type": "string"}}, "required": ["op", "type", "after"],
             "additionalProperties": False},
            {"type": "object", "properties": {"op": {"const": "connect"}, "from": {"type": "string"},
             "from_port": {"type": "string"}, "to": {"type": "string"}, "to_port": {"type": "string"}},
             "required": ["op", "from", "to"], "additionalProperties": False},
            {"type": "object", "properties": {"op": {"const": "disconnect"}, "stream": {"type": "string"}},
             "required": ["op", "stream"], "additionalProperties": False},
            {"type": "object", "properties": {"op": {"const": "mirror"}, "target": {"type": "string"},
             "axis": {"enum": ["horizontal", "vertical"]}}, "required": ["op", "target", "axis"],
             "additionalProperties": False},
            {"type": "object", "properties": {"op": {"const": "move"}, "target": {"type": "string"},
             "dx": {"type": "number"}, "dy": {"type": "number"}}, "required": ["op", "target", "dx", "dy"],
             "additionalProperties": False},
            {"type": "object", "properties": {"op": {"const": "rename"}, "target": {"type": "string"},
             "new_tag": {"type": "string"}}, "required": ["op", "target", "new_tag"], "additionalProperties": False},
            {"type": "object", "properties": {"op": {"const": "delete"}, "target": {"type": "string"}},
             "required": ["op", "target"], "additionalProperties": False}
        ]}},
        "rationale": {"type": "string", "maxLength": 600}},
        "required": ["grant_id", "base_revision", "actions"], "additionalProperties": False},
}
_BLUECAD_READ_TOOL = {
    "name": "jarvis_bluecad_read", "description": "Read the current BLUECAD candidate and selected parts.",
    "inputSchema": {"type": "object", "properties": {"grant_id": {"type": "string", "maxLength": 128},
                     },
                     "required": ["grant_id"], "additionalProperties": False},
}
_BLUECAD_ACT_TOOL = {
    "name": "jarvis_bluecad_act",
    "description": "Request a typed BLUECAD candidate change such as duplicate_part, set_part_param, move_part or delete_part.",
    "inputSchema": {"type": "object", "properties": {
        "grant_id": {"type": "string", "maxLength": 128},
        "base_revision": {"type": "string", "maxLength": 64},
        "actions": {"type": "array", "minItems": 1, "maxItems": 8, "items": {"oneOf": [
            {"type": "object", "properties": {"op": {"const": "duplicate_part"}, "part": {"type": "string"},
             "placement": {"enum": ["beside", "above", "along"]}, "gap_mm": {"type": "number"}},
             "required": ["op", "part"], "additionalProperties": False},
            {"type": "object", "properties": {"op": {"const": "set_part_param"}, "part": {"type": "string"},
             "param": {"type": "string"}, "value": {"type": "number"},
             "unit": {"enum": ["mm", "m", "cm", "deg"]}},
             "required": ["op", "part", "param", "value", "unit"], "additionalProperties": False},
            {"type": "object", "properties": {"op": {"const": "move_part"}, "part": {"type": "string"},
             "dx": {"type": "number"}, "dy": {"type": "number"}, "dz": {"type": "number"},
             "unit": {"enum": ["mm", "m", "cm"]}}, "required": ["op", "part"], "additionalProperties": False},
            {"type": "object", "properties": {"op": {"const": "delete_part"}, "part": {"type": "string"}},
             "required": ["op", "part"], "additionalProperties": False}
        ]}},
        "rationale": {"type": "string", "maxLength": 600}},
        "required": ["grant_id", "base_revision", "actions"], "additionalProperties": False},
}
_TOOLS = [_TOOL, _RETRIEVAL_TOOL, _DECISION_TOOL, _PROCESS_READ_TOOL, _PROCESS_ACT_TOOL,
          _BLUECAD_READ_TOOL, _BLUECAD_ACT_TOOL]
_NAMED = {tool["name"] for tool in _TOOLS if tool is not _TOOL}


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
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": _TOOLS}}
    if method == "tools/call":
        params = message.get("params") or {}
        if params.get("name") not in {tool["name"] for tool in _TOOLS}:
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "unknown tool"}}
        body = params.get("arguments") or {}
        if params.get("name") in _NAMED and isinstance(body, dict):
            body = {**body, "tool_name": params["name"]}
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
