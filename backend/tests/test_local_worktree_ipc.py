from __future__ import annotations

import importlib.util
import inspect
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load_script(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


repository_delivery = load_script("repository_delivery")
actuator = load_script("local_worktree_actuator")
ipc = load_script("local_worktree_ipc")

Capability = actuator.Capability
RequestContext = actuator.RequestContext
WorkerState = actuator.WorkerState
IPC_PROTOCOL = ipc.IPC_PROTOCOL
IPCRefusal = ipc.IPCRefusal
LocalIPCServer = ipc.LocalIPCServer
_decode_json_payload = ipc._decode_json_payload
_encode_json_payload = ipc._encode_json_payload
endpoint_for = ipc.endpoint_for
ipc_authkey = ipc.ipc_authkey
parse_request = ipc.parse_request
request_once = ipc.request_once


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


def test_server_owned_capability_blocks_client_self_promotion(tmp_path: Path) -> None:
    state = WorkerState(tmp_path / "worker", worker_id="worker-test")

    class StubActuator:
        def __init__(self, worker_state: WorkerState) -> None:
            self.state = worker_state

    server = LocalIPCServer(
        StubActuator(state),  # type: ignore[arg-type]
        admitted_capabilities={
            ("principal-1", "session-1"): Capability.REVIEWER,
        },
    )
    requested = RequestContext(
        "req-1",
        "principal-1",
        "session-1",
        Capability.IMPLEMENTER,
    )
    admitted = server._admit_context(requested)
    assert admitted.capability is Capability.REVIEWER

    unregistered = RequestContext(
        "req-2",
        "principal-2",
        "session-2",
        Capability.IMPLEMENTER,
    )
    with pytest.raises(IPCRefusal, match="server-owned capability"):
        server._admit_context(unregistered)


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
