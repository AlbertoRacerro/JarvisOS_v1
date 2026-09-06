from __future__ import annotations

import inspect
import os
from pathlib import Path

import pytest

from scripts.local_worktree_actuator import Capability, WorkerState
from scripts.local_worktree_ipc import (
    IPC_PROTOCOL,
    IPCRefusal,
    LocalIPCServer,
    _decode_json_payload,
    _encode_json_payload,
    endpoint_for,
    ipc_authkey,
    parse_request,
    request_once,
)


def _request() -> dict[str, object]:
    return {
        "protocol": IPC_PROTOCOL,
        "context": {
            "request_id": "req-1",
            "principal_id": "principal-1",
            "session_id": "session-1",
            "capability": Capability.OBSERVER.value,
        },
        "operation": "worker_health",
        "arguments": {},
    }


def test_request_codec_is_bounded_json_and_rejects_pickle_bytes() -> None:
    payload = _encode_json_payload(_request(), limit=256 * 1024, label="request")
    decoded = _decode_json_payload(payload, limit=256 * 1024, label="request")
    ctx, operation, arguments = parse_request(decoded)
    assert ctx.capability is Capability.OBSERVER
    assert operation == "worker_health"
    assert arguments == {}

    with pytest.raises(IPCRefusal):
        _decode_json_payload(b"\x80\x04N.", limit=256 * 1024, label="request")


def test_wire_path_never_calls_pickle_recv_or_send() -> None:
    server_source = inspect.getsource(LocalIPCServer.serve_once)
    client_source = inspect.getsource(request_once)
    assert ".recv(" not in server_source
    assert ".send(" not in server_source
    assert ".recv(" not in client_source
    assert ".send(" not in client_source
    assert "recv_bytes" in server_source and "send_bytes" in server_source
    assert "recv_bytes" in client_source and "send_bytes" in client_source


def test_request_shape_is_closed() -> None:
    request = _request()
    request["unexpected"] = True
    with pytest.raises(IPCRefusal, match="envelope"):
        parse_request(request)

    request = _request()
    assert isinstance(request["context"], dict)
    request["context"]["capability"] = "root"
    with pytest.raises(IPCRefusal, match="capability"):
        parse_request(request)


def test_endpoint_and_auth_state_are_local_and_private(tmp_path: Path) -> None:
    state = WorkerState(tmp_path / "worker", worker_id="worker-test")
    address, family = endpoint_for(state)
    if os.name == "nt":
        assert family == "AF_PIPE"
        assert address.startswith(r"\\.\pipe\jarvisos-local-worktree-")
    else:
        assert family == "AF_UNIX"
        assert Path(address).parent == state.root

    first = ipc_authkey(state)
    second = ipc_authkey(state)
    assert first == second
    assert len(first) == 32
    if os.name != "nt":
        assert (state.root / "ipc-auth.bin").stat().st_mode & 0o077 == 0
