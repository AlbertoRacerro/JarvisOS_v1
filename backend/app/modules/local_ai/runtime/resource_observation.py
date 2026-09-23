"""Bounded, best-effort observations for the in-process resource arbiter."""

from __future__ import annotations

import shutil
import subprocess
from datetime import UTC, datetime

from app.modules.local_ai.resource_contracts import (
    CpuState,
    GpuState,
    LoadedModelState,
    MemoryState,
    RuntimeResourceSnapshot,
)
from app.modules.local_ai.runtime.status import get_local_ai_runtime_status


def parse_nvidia_smi(text: str) -> tuple[GpuState, ...]:
    """Parse index,name,total MiB,used MiB CSV; malformed rows provide no capacity."""
    result: list[GpuState] = []
    for line in text.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 4:
            continue
        try:
            index, total, used = int(parts[0]), int(parts[2]), int(parts[3])
            if index < 0 or total < 0 or used < 0 or used > total or not parts[1]:
                continue
            result.append(
                GpuState(index=index, name=parts[1], vram_total_bytes=total * 1024**2, vram_used_bytes=used * 1024**2)
            )
        except ValueError:
            continue
    return tuple(result)


def query_gpus() -> tuple[GpuState, ...]:
    binary = shutil.which("nvidia-smi")
    if binary is None:
        return ()
    try:
        result = subprocess.run(
            [binary, "--query-gpu=index,name,memory.total,memory.used", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=1.5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ()
    return parse_nvidia_smi(result.stdout) if result.returncode == 0 else ()


def observe_resources() -> RuntimeResourceSnapshot:
    status = get_local_ai_runtime_status()
    models: list[LoadedModelState] = []
    if status.get("ps_error_type") is None and status.get("ollama_reachable"):
        for item in status.get("loaded_models", []):
            if isinstance(item, dict) and isinstance(item.get("name"), str):
                models.append(
                    LoadedModelState(
                        name=item["name"],
                        size_bytes=item.get("size"),
                        vram_bytes=item.get("size_vram"),
                        processor=item.get("processor"),
                        keep_alive_until=item.get("until"),
                    )
                )
    # RAM/CPU availability is not exposed by the current runtime probe.
    return RuntimeResourceSnapshot(
        generation=0,
        observed_at=datetime.now(UTC),
        cpu=CpuState(),
        memory=MemoryState(),
        gpus=query_gpus(),
        loaded_models=tuple(models),
    )
