#!/usr/bin/env python3
"""Current-user local IPC adapter for spec 141.

This transport is deliberately smaller than a general agent/RPC service. It
exposes only ``LocalWorktreeActuator.dispatch`` over an OS-local endpoint:
AF_PIPE on Windows or AF_UNIX inside the worker-private state directory on
POSIX. It never opens TCP, accepts argv/process requests, owns credentials, or
adds capabilities beyond the actuator's fixed dispatch table.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
from dataclasses import asdict, is_dataclass
from enum import Enum
from multiprocessing.connection import Client, Listener
from pathlib import Path
from typing import Any, Callable

try:
    from scripts.local_worktree_actuator import (
        ActuatorRefusal,
        Capability,
        LocalWorktreeActuator,
        RequestContext,
        WorkerState,
    )
    from scripts.repository_delivery import DeliveryRefusal
except ImportError:  # direct script-style import
    from local_worktree_actuator import (  # type: ignore[no-redef]
        ActuatorRefusal,
        Capability,
        LocalWorktreeActuator,
        RequestContext,
        WorkerState,
    )
    from repository_delivery import DeliveryRefusal  # type: ignore[no-redef]

MAX_REQUEST_BYTES = 256 * 1024
MAX_RESPONSE_BYTES = 512 * 1024
IPC_KEY_BYTES = 32
IPC_KEY_FILE = "ipc-auth.bin"
IPC_PROTOCOL = "jarvisos-local-worktree-v1"

# Maintainer activation may provide a fixed verifier that inspects the actual
# Listener/named-pipe security descriptor. It is deliberately not request/IPC
# addressable. Returning anything except literal True fails activation closed.
WindowsBoundaryVerifier = Callable[[Any, "WorkerState", str], bool]


class IPCRefusal(RuntimeError):
    pass


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise IPCRefusal("response type is not serializable by the bounded protocol")


def _principal_tag() -> str:
    if os.name == "nt":
        principal = os.environ.get("USERNAME", "")
    else:
        principal = str(os.getuid())
    return hashlib.sha256(principal.encode("utf-8")).hexdigest()[:16]


def endpoint_for(state: WorkerState) -> tuple[str, str]:
    """Return a fixed local endpoint and family; never AF_INET/TCP."""

    suffix = hashlib.sha256(
        f"{_principal_tag()}:{state.worker_id}".encode("utf-8")
    ).hexdigest()[:20]
    if os.name == "nt":
        local_appdata = os.environ.get("LOCALAPPDATA")
        if not local_appdata:
            raise IPCRefusal("LOCALAPPDATA is required for current-user IPC activation")
        root = state.root.resolve()
        try:
            root.relative_to(Path(local_appdata).resolve())
        except ValueError as exc:
            raise IPCRefusal("Windows worker state must live under LOCALAPPDATA") from exc
        return rf"\\.\pipe\jarvisos-local-worktree-{suffix}", "AF_PIPE"
    return str(state.root / f"ipc-{suffix}.sock"), "AF_UNIX"


def ipc_authkey(state: WorkerState) -> bytes:
    """Create/read a worker-private transport key; never return it over IPC."""

    path = state.root / IPC_KEY_FILE
    if not path.exists():
        data = secrets.token_bytes(IPC_KEY_BYTES)
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    data = path.read_bytes()
    if len(data) != IPC_KEY_BYTES:
        raise IPCRefusal("IPC authentication state is corrupt")
    if os.name != "nt" and path.stat().st_mode & 0o077:
        raise IPCRefusal("IPC authentication state is not private")
    return data


def _decode_json_payload(payload: bytes, *, limit: int, label: str) -> Any:
    if len(payload) > limit:
        raise IPCRefusal(f"{label} exceeds bounded IPC payload")
    try:
        text = payload.decode("utf-8")
        return json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IPCRefusal(f"{label} is not valid UTF-8 JSON") from exc


def _encode_json_payload(value: Any, *, limit: int, label: str) -> bytes:
    try:
        payload = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise IPCRefusal(f"{label} is not JSON serializable") from exc
    if len(payload) > limit:
        raise IPCRefusal(f"{label} exceeds bounded IPC payload")
    return payload


def parse_request(raw: Any) -> tuple[RequestContext, str, dict[str, Any]]:
    """Validate the bounded wire request; capability remains only requested metadata."""

    _encode_json_payload(raw, limit=MAX_REQUEST_BYTES, label="request")
    if not isinstance(raw, dict) or set(raw) != {"protocol", "context", "operation", "arguments"}:
        raise IPCRefusal("request envelope is invalid")
    if raw["protocol"] != IPC_PROTOCOL:
        raise IPCRefusal("unsupported IPC protocol")
    context = raw["context"]
    if not isinstance(context, dict) or set(context) != {
        "request_id",
        "principal_id",
        "session_id",
        "capability",
    }:
        raise IPCRefusal("request context is invalid")
    if not all(isinstance(context[key], str) and context[key] for key in context):
        raise IPCRefusal("request context fields must be non-empty strings")
    try:
        requested_capability = Capability(context["capability"])
    except ValueError as exc:
        raise IPCRefusal("unknown capability") from exc
    operation = raw["operation"]
    arguments = raw["arguments"]
    if not isinstance(operation, str) or not operation or not isinstance(arguments, dict):
        raise IPCRefusal("operation/arguments shape is invalid")
    return (
        RequestContext(
            context["request_id"],
            context["principal_id"],
            context["session_id"],
            requested_capability,
        ),
        operation,
        arguments,
    )


class LocalIPCServer:
    def __init__(
        self,
        actuator: LocalWorktreeActuator,
        *,
        admitted_capabilities: dict[tuple[str, str], Capability] | None = None,
        windows_boundary_verifier: WindowsBoundaryVerifier | None = None,
    ) -> None:
        self.actuator = actuator
        self.address, self.family = endpoint_for(actuator.state)
        self.authkey = ipc_authkey(actuator.state)
        # Maintainer activation owns this mapping. It is never populated or
        # modified from request arguments, so a caller cannot self-promote.
        self._admitted_capabilities = dict(admitted_capabilities or {})
        self._windows_boundary_verifier = windows_boundary_verifier

    def _admit_context(self, requested: RequestContext) -> RequestContext:
        capability = self._admitted_capabilities.get(
            (requested.principal_id, requested.session_id)
        )
        if capability is None:
            raise IPCRefusal("principal/session has no server-owned capability admission")
        return RequestContext(
            requested.request_id,
            requested.principal_id,
            requested.session_id,
            capability,
        )

    def _verify_transport_boundary(self, listener: Any) -> None:
        if self.family != "AF_PIPE":
            return
        verifier = self._windows_boundary_verifier
        if verifier is None:
            raise IPCRefusal(
                "Windows IPC activation requires current-user named-pipe ACL verification"
            )
        try:
            verified = verifier(listener, self.actuator.state, self.address)
        except Exception as exc:  # activation verifier must fail closed
            raise IPCRefusal("Windows current-user IPC boundary verification failed") from exc
        if verified is not True:
            raise IPCRefusal("Windows current-user IPC boundary is not verified")

    def serve_once(self) -> None:
        """Serve exactly one request; lifecycle/restart ownership stays external."""

        if self.family == "AF_UNIX":
            Path(self.address).unlink(missing_ok=True)
        listener = Listener(self.address, family=self.family, authkey=self.authkey)
        try:
            # Critical ordering: on Windows inspect/prove the *actual created*
            # named-pipe boundary before accepting any peer. A host without a
            # maintainer-owned verifier has no Windows local-worker capability;
            # cloud/GitHub lanes remain independent and usable.
            self._verify_transport_boundary(listener)
            if self.family == "AF_UNIX":
                Path(self.address).chmod(0o600)
            connection = listener.accept()
            try:
                try:
                    raw = _decode_json_payload(
                        connection.recv_bytes(MAX_REQUEST_BYTES + 1),
                        limit=MAX_REQUEST_BYTES,
                        label="request",
                    )
                    requested_ctx, operation, arguments = parse_request(raw)
                    ctx = self._admit_context(requested_ctx)
                    result = self.actuator.dispatch(ctx, operation, **arguments)
                    response = {"ok": True, "result": _jsonable(result)}
                except (IPCRefusal, ActuatorRefusal, DeliveryRefusal, TypeError, OSError) as exc:
                    code = getattr(getattr(exc, "code", None), "value", None)
                    response = {
                        "ok": False,
                        "code": code or "IPC_REFUSED",
                        "message": str(exc),
                    }
                connection.send_bytes(
                    _encode_json_payload(
                        response,
                        limit=MAX_RESPONSE_BYTES,
                        label="response",
                    )
                )
            finally:
                connection.close()
        finally:
            listener.close()
            if self.family == "AF_UNIX":
                Path(self.address).unlink(missing_ok=True)


def request_once(state: WorkerState, request: dict[str, Any]) -> dict[str, Any]:
    """Small test/client adapter using the same fixed local endpoint and auth key."""

    address, family = endpoint_for(state)
    connection = Client(address, family=family, authkey=ipc_authkey(state))
    try:
        connection.send_bytes(
            _encode_json_payload(request, limit=MAX_REQUEST_BYTES, label="request")
        )
        response = _decode_json_payload(
            connection.recv_bytes(MAX_RESPONSE_BYTES + 1),
            limit=MAX_RESPONSE_BYTES,
            label="response",
        )
    finally:
        connection.close()
    if not isinstance(response, dict):
        raise IPCRefusal("invalid IPC response")
    return response


__all__ = [
    "IPC_PROTOCOL",
    "IPCRefusal",
    "LocalIPCServer",
    "WindowsBoundaryVerifier",
    "endpoint_for",
    "ipc_authkey",
    "parse_request",
    "request_once",
]
