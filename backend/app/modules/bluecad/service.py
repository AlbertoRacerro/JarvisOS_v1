"""BLUECAD CAD adapter public build API."""

from __future__ import annotations

import json
import multiprocessing as mp
import queue
from pathlib import Path
from typing import Any

from app.modules.bluecad.export import build_artifacts
from app.modules.bluecad.models import BluecadError, BuildResult
from app.modules.bluecad.spec import SpecValidationError, canonicalize_geometry_spec, load_geometry_spec
from app.modules.bluecad.validate import write_validation_report

DEFAULT_TIMEOUT_SECONDS = 30.0


def build_geometry_spec(spec: dict[str, Any], out_dir: str | Path, *, timeout_s: float = DEFAULT_TIMEOUT_SECONDS) -> BuildResult:
    canonical = canonicalize_geometry_spec(spec)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    result_queue: mp.Queue[dict[str, Any]] = mp.Queue()
    process = mp.Process(target=_worker, args=(canonical, str(out_path), result_queue), daemon=True)
    process.start()
    process.join(timeout_s)
    if process.is_alive():
        process.kill()
        process.join()
        error = BluecadError("TIMEOUT", {"timeout_s": timeout_s})
        report = write_validation_report(canonical, out_path, error=error)
        return BuildResult(canonical["spec_id"], out_path, None, out_path / "validation_report.json", None, report, "error", [error.as_report_error()])
    try:
        payload = result_queue.get_nowait()
    except queue.Empty:
        error = BluecadError("KERNEL_ERROR", {"message": "worker exited without returning a result", "exitcode": process.exitcode})
        report = write_validation_report(canonical, out_path, error=error)
        return BuildResult(canonical["spec_id"], out_path, None, out_path / "validation_report.json", None, report, "error", [error.as_report_error()])
    if payload["ok"]:
        manifest = payload["manifest"]
        report = write_validation_report(canonical, out_path)
        return BuildResult(canonical["spec_id"], out_path, out_path / "manifest.json", out_path / "validation_report.json", manifest, report, report["verdict"])
    error = BluecadError(payload["code"], payload["detail"])
    report = write_validation_report(canonical, out_path, error=error)
    return BuildResult(canonical["spec_id"], out_path, None, out_path / "validation_report.json", None, report, "error", [error.as_report_error()])


def build_geometry_spec_file(spec_path: str | Path, out_dir: str | Path, *, timeout_s: float = DEFAULT_TIMEOUT_SECONDS) -> BuildResult:
    try:
        spec = load_geometry_spec(spec_path)
    except SpecValidationError as exc:
        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        report = {
            "report_version": "bluecad_validation_report_v0_1",
            "spec_id": "sha256:" + "0" * 64,
            "manifest_sha256": None,
            "verdict": "error",
            "checks": [],
            "errors": [{"code": exc.code, "detail": exc.detail}],
        }
        report_path = out_path / "validation_report.json"
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return BuildResult(report["spec_id"], out_path, None, report_path, None, report, "error", report["errors"])
    return build_geometry_spec(spec, out_dir, timeout_s=timeout_s)


def _worker(spec: dict[str, Any], out_dir: str, result_queue: mp.Queue[dict[str, Any]]) -> None:
    try:
        manifest = build_artifacts(spec, out_dir)
    except BluecadError as exc:
        result_queue.put({"ok": False, "code": exc.code, "detail": exc.detail})
    except Exception as exc:  # pragma: no cover - kernel crash/error protection
        result_queue.put({"ok": False, "code": "KERNEL_ERROR", "detail": {"message": str(exc), "type": type(exc).__name__}})
    else:
        result_queue.put({"ok": True, "manifest": manifest})
