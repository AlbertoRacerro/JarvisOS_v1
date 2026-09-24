"""Bounded, best-effort observations for the in-process resource arbiter."""

from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

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


def parse_linux_meminfo(text: str) -> MemoryState:
    """Read physical RAM capacity in kB; malformed or missing values stay unknown."""
    values: dict[str, int] = {}
    for line in text.splitlines():
        key, separator, value = line.partition(":")
        if not separator or key not in {"MemTotal", "MemAvailable"}:
            continue
        parts = value.split()
        if len(parts) != 2 or parts[1] != "kB" or not parts[0].isdecimal():
            continue
        values[key] = int(parts[0]) * 1024
    total = values.get("MemTotal")
    available = values.get("MemAvailable")
    if total is not None and available is not None and available > total:
        available = None
    return MemoryState(total_bytes=total, available_bytes=available)


def _windows_memory() -> MemoryState:
    class MemoryStatus(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    try:
        status = MemoryStatus()
        status.dwLength = ctypes.sizeof(MemoryStatus)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
        if not kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return MemoryState()
        return MemoryState(total_bytes=status.ullTotalPhys, available_bytes=status.ullAvailPhys)
    except (AttributeError, OSError, ValueError):
        return MemoryState()


def query_memory() -> MemoryState:
    if sys.platform == "linux":
        try:
            return parse_linux_meminfo(Path("/proc/meminfo").read_text(encoding="ascii"))
        except (OSError, UnicodeError):
            return MemoryState()
    if sys.platform == "win32":
        return _windows_memory()
    return MemoryState()


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
    return RuntimeResourceSnapshot(
        generation=0,
        observed_at=datetime.now(UTC),
        cpu=CpuState(logical_cores=os.cpu_count()),
        memory=query_memory(),
        gpus=query_gpus(),
        loaded_models=tuple(models),
    )
