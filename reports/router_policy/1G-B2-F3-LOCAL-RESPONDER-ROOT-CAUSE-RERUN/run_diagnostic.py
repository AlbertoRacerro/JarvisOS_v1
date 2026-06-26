from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPORT_DIR = Path(__file__).resolve().parent
REPO_ROOT = REPORT_DIR.parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
SCRIPTS_DIR = REPO_ROOT / "scripts"
for path in (BACKEND_DIR, SCRIPTS_DIR):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

OLLAMA_URL = "http://127.0.0.1:11434"
GENERATE_URL = f"{OLLAMA_URL}/api/generate"
PROBLEM_PROMPT = "dimensioniamo concettualmente una pompa centrifuga per un fotobioreattore: prevalenza, portata, NPSH"
SHORT_CONTROL_PROMPT = "ciao"
BLUEREV_IP_PROMPT = (
    "usa i parametri proprietari BlueRev per dimensionare concettualmente una pompa centrifuga: prevalenza, portata, NPSH"
)
BLUEREV_GENERIC_PROMPT = "dimensioniamo concettualmente una pompa centrifuga per BlueRev: prevalenza, portata, NPSH"
GEMMA_MODEL = "gemma4:12b-it-qat"
QWEN_MODEL = "qwen3:14b"
TIMEOUT_S = 120.0
MAX_STREAM_CHUNKS = 512
PS_INTERVAL_S = 5.0


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_command(args: list[str], *, timeout: float = 10.0) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            args,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        return {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "duration_ms": round((time.perf_counter() - started) * 1000, 3),
        }
    except Exception as exc:
        return {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "duration_ms": round((time.perf_counter() - started) * 1000, 3),
        }


def http_json(url: str, *, timeout: float = 5.0) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            status = getattr(response, "status", response.getcode())
            body = response.read().decode("utf-8", errors="replace")
        decoded = json.loads(body)
        return {
            "ok": True,
            "status": status,
            "body": decoded,
            "duration_ms": round((time.perf_counter() - started) * 1000, 3),
        }
    except Exception as exc:
        return {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "duration_ms": round((time.perf_counter() - started) * 1000, 3),
        }


def ollama_tags() -> dict[str, Any]:
    return http_json(f"{OLLAMA_URL}/api/tags")


def model_names(tags_result: dict[str, Any]) -> list[str]:
    body = tags_result.get("body")
    if not isinstance(body, dict):
        return []
    models = body.get("models")
    if not isinstance(models, list):
        return []
    names = []
    for model in models:
        if isinstance(model, dict) and isinstance(model.get("name"), str):
            names.append(model["name"])
    return names


def capture_ollama_ps(label: str) -> dict[str, Any]:
    result = run_command(["ollama", "ps"], timeout=10.0)
    return {
        "label": label,
        "timestamp": utc_now(),
        "command": "ollama ps",
        **result,
        "parsed_rows": parse_ollama_ps(result.get("stdout", "")),
    }


def parse_ollama_ps(output: str) -> list[dict[str, str]]:
    lines = [line.rstrip() for line in output.splitlines() if line.strip()]
    if len(lines) < 2:
        return []
    rows: list[dict[str, str]] = []
    for line in lines[1:]:
        parts = line.split()
        if len(parts) < 5:
            rows.append({"raw": line})
            continue
        processor = parts[4]
        context_index = 5
        if len(parts) > 5 and parts[5].upper() in {"GPU", "CPU"}:
            processor = f"{parts[4]} {parts[5]}"
            context_index = 6
        rows.append(
            {
                "MODEL": parts[0],
                "ID": parts[1],
                "SIZE": " ".join(parts[2:4]),
                "PROCESSOR": processor,
                "CONTEXT": parts[context_index] if len(parts) > context_index else "",
                "UNTIL": " ".join(parts[context_index + 1 :]) if len(parts) > context_index + 1 else "",
                "raw": line,
            }
        )
    return rows


class PsMonitor:
    def __init__(self, label: str):
        self.label = label
        self.snapshots: list[dict[str, Any]] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def __enter__(self) -> "PsMonitor":
        self.snapshots.append(capture_ollama_ps(f"{self.label}:before_run"))
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._stop.set()
        self._thread.join(timeout=PS_INTERVAL_S + 2)
        self.snapshots.append(capture_ollama_ps(f"{self.label}:after_run"))

    def _run(self) -> None:
        index = 0
        while not self._stop.wait(PS_INTERVAL_S):
            index += 1
            self.snapshots.append(capture_ollama_ps(f"{self.label}:during_{index:03d}"))


def visible_text(text: str) -> str:
    return "".join(ch for ch in text if not ch.isspace())


def direct_stream_generate(model: str, prompt: str, label: str) -> dict[str, Any]:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "keep_alive": "30m",
    }
    encoded = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        GENERATE_URL,
        data=encoded,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    chunks: list[dict[str, Any]] = []
    total_text = ""
    first_chunk_ms = None
    first_visible_text_ms = None
    visible_after_64 = None
    visible_after_512 = None
    empty_or_whitespace_chunks = 0
    final_metadata: dict[str, Any] = {}
    stopped_reason = "unknown"
    exception: dict[str, Any] | None = None
    status = None
    monitor: PsMonitor
    with PsMonitor(label) as monitor:
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_S + 5) as response:
                status = getattr(response, "status", response.getcode())
                while True:
                    elapsed = time.perf_counter() - started
                    if elapsed >= TIMEOUT_S:
                        stopped_reason = "timeout_120s"
                        break
                    if len(chunks) >= MAX_STREAM_CHUNKS:
                        stopped_reason = "max_512_chunks"
                        break
                    line = response.readline()
                    if not line:
                        stopped_reason = "eof"
                        break
                    now_ms = round((time.perf_counter() - started) * 1000, 3)
                    if first_chunk_ms is None:
                        first_chunk_ms = now_ms
                    raw_line = line.decode("utf-8", errors="replace").strip()
                    try:
                        decoded = json.loads(raw_line)
                    except json.JSONDecodeError:
                        decoded = {"raw_unparsed": raw_line}
                    response_text = decoded.get("response") if isinstance(decoded, dict) else None
                    if not isinstance(response_text, str):
                        response_text = ""
                    total_text += response_text
                    if not visible_text(response_text):
                        empty_or_whitespace_chunks += 1
                    if first_visible_text_ms is None and visible_text(total_text):
                        first_visible_text_ms = now_ms
                    if len(chunks) == 63:
                        visible_after_64 = len(visible_text(total_text))
                    if len(chunks) == 511:
                        visible_after_512 = len(visible_text(total_text))
                    if isinstance(decoded, dict) and decoded.get("done") is True:
                        for key in (
                            "total_duration",
                            "load_duration",
                            "prompt_eval_count",
                            "prompt_eval_duration",
                            "eval_count",
                            "eval_duration",
                            "done_reason",
                        ):
                            if key in decoded:
                                final_metadata[key] = decoded[key]
                        stopped_reason = "completed"
                    chunks.append(
                        {
                            "index": len(chunks) + 1,
                            "at_ms": now_ms,
                            "response": response_text,
                            "done": decoded.get("done") if isinstance(decoded, dict) else None,
                            "eval_count": decoded.get("eval_count") if isinstance(decoded, dict) else None,
                            "done_reason": decoded.get("done_reason") if isinstance(decoded, dict) else None,
                        }
                    )
                    if stopped_reason == "completed":
                        break
        except Exception as exc:
            stopped_reason = "exception"
            exception = {"error_type": type(exc).__name__, "error": str(exc)}
    if visible_after_64 is None:
        visible_after_64 = len(visible_text(total_text)) if len(chunks) < 64 else 0
    if visible_after_512 is None:
        visible_after_512 = len(visible_text(total_text))
    wall_clock_ms = round((time.perf_counter() - started) * 1000, 3)
    return {
        "label": label,
        "model": model,
        "prompt": prompt,
        "http_status": status,
        "wall_clock_ms": wall_clock_ms,
        "time_to_first_chunk_ms": first_chunk_ms,
        "time_to_first_visible_text_ms": first_visible_text_ms,
        "visible_text_chars_after_64_chunks": visible_after_64,
        "visible_text_chars_after_512_chunks": visible_after_512,
        "total_visible_chars": len(visible_text(total_text)),
        "total_response_chars": len(total_text),
        "chunks_captured": len(chunks),
        "empty_or_whitespace_chunks": empty_or_whitespace_chunks,
        "stopped_reason": stopped_reason,
        "exception": exception,
        "final_metadata": final_metadata,
        "first_512_chunks": chunks,
        "text_preview": total_text[:1200],
        "output_characterization": characterize_output(total_text, chunks),
        "ollama_ps_snapshots": monitor.snapshots,
    }


def characterize_output(text: str, chunks: list[dict[str, Any]]) -> str:
    visible = visible_text(text)
    if not visible:
        return "no_visible_text"
    lowered = text.lower()
    useful_terms = ("pompa", "prevalenza", "portata", "npsh", "centrifuga")
    if any(term in lowered for term in useful_terms):
        return "useful_visible_text"
    if len(chunks) >= 64 and len(visible) < 20:
        return "prefix_or_hidden_like"
    return "visible_text_unclear"


def warmup_model(model: str) -> dict[str, Any]:
    payload = {
        "model": model,
        "prompt": "ciao",
        "stream": False,
        "keep_alive": "30m",
        "options": {"temperature": 0, "num_predict": 64},
    }
    encoded = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        GENERATE_URL,
        data=encoded,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            status = getattr(response, "status", response.getcode())
            body = response.read().decode("utf-8", errors="replace")
        decoded = json.loads(body)
        return {
            "ok": True,
            "status": status,
            "duration_ms": round((time.perf_counter() - started) * 1000, 3),
            "response_char_count": len(decoded.get("response", "")) if isinstance(decoded, dict) else None,
            "timing": extract_timing(decoded if isinstance(decoded, dict) else {}),
        }
    except Exception as exc:
        return {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "duration_ms": round((time.perf_counter() - started) * 1000, 3),
        }


def extract_timing(decoded: dict[str, Any]) -> dict[str, Any]:
    return {
        key: decoded[key]
        for key in (
            "total_duration",
            "load_duration",
            "prompt_eval_count",
            "prompt_eval_duration",
            "eval_count",
            "eval_duration",
            "done_reason",
        )
        if key in decoded
    }


def setup_backend_env(model: str) -> None:
    os.environ["JARVISOS_DATA_ROOT"] = tempfile.mkdtemp(prefix="jarvisos-root-cause-rerun-")
    os.environ["JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE"] = "1"
    os.environ["JARVISOS_DEV_MESSAGE_ROUTE_ASSUME_PUBLIC_SIMPLE"] = "1"
    os.environ["JARVISOS_DEV_MESSAGE_ROUTE_ALLOW_LOCAL_RESPONDER"] = "1"
    os.environ["JARVISOS_DEV_MESSAGE_ROUTE_MODEL"] = model
    os.environ["JARVISOS_DEV_MESSAGE_ROUTE_TIMEOUT_S"] = str(int(TIMEOUT_S))
    os.environ["JARVISOS_DEV_MESSAGE_ROUTE_KEEP_ALIVE"] = "30m"
    os.environ.pop("JARVISOS_DEV_MESSAGE_ROUTE_NUM_PREDICT", None)


def backend_local_chat_cases(model: str) -> list[dict[str, Any]]:
    setup_backend_env(model)
    from fastapi.testclient import TestClient
    from app.core.bootstrap import initialize_storage
    from app.core.config import get_settings
    from app.main import create_app

    get_settings.cache_clear()
    initialize_storage(seed_default=True)
    client = TestClient(create_app())
    cases = [
        ("problematic", PROBLEM_PROMPT),
        ("short_control", SHORT_CONTROL_PROMPT),
        ("bluerev_ip_control", BLUEREV_IP_PROMPT),
        ("bluerev_generic_control", BLUEREV_GENERIC_PROMPT),
    ]
    results: list[dict[str, Any]] = []
    try:
        for label, prompt in cases:
            started = time.perf_counter()
            with PsMonitor(f"backend_{label}") as monitor:
                try:
                    response = client.post("/api/dev/local-chat", json={"message": prompt})
                    http_status = response.status_code
                    try:
                        body = response.json()
                    except Exception as exc:
                        body = {"json_parse_error": type(exc).__name__, "text": response.text[:1000]}
                    exception = None
                except Exception as exc:
                    http_status = None
                    body = {}
                    exception = {"error_type": type(exc).__name__, "error": str(exc)}
            wall_clock_ms = round((time.perf_counter() - started) * 1000, 3)
            results.append(
                {
                    "label": label,
                    "prompt": prompt,
                    "model": model,
                    "http_status": http_status,
                    "wall_clock_ms": wall_clock_ms,
                    "trace_id": body.get("trace_id") if isinstance(body, dict) else None,
                    "executed": body.get("executed") if isinstance(body, dict) else None,
                    "reason": body.get("reason") if isinstance(body, dict) else None,
                    "error_type": body.get("error_type") if isinstance(body, dict) else None,
                    "decision_summary": body.get("decision_summary") if isinstance(body, dict) else None,
                    "backend_timing": body.get("backend_timing") if isinstance(body, dict) else None,
                    "local_responder_timing": body.get("local_responder_timing") if isinstance(body, dict) else None,
                    "response_char_count_returned": body.get("response_char_count_returned") if isinstance(body, dict) else None,
                    "response_truncated": body.get("response_truncated") if isinstance(body, dict) else None,
                    "body": body,
                    "exception": exception,
                    "ollama_ps_snapshots": monitor.snapshots,
                }
            )
    finally:
        client.close()
        get_settings.cache_clear()
    return results


def processor_classes(ps_snapshots: list[dict[str, Any]], model: str) -> list[str]:
    classes = []
    for snapshot in ps_snapshots:
        for row in snapshot.get("parsed_rows", []):
            if row.get("MODEL") == model:
                processor = row.get("PROCESSOR", "")
                if processor:
                    classes.append(processor)
    return classes


def classify_processor(processors: list[str]) -> str:
    if not processors:
        return "unknown"
    joined = " ".join(processors).lower()
    if "cpu" in joined and "gpu" in joined:
        return "partial GPU/CPU"
    if "cpu" in joined:
        return "CPU"
    if "100% gpu" in joined or all("gpu" in item.lower() and "cpu" not in item.lower() for item in processors):
        return "100% GPU"
    return "unknown"


def build_summary(raw: dict[str, Any]) -> dict[str, Any]:
    gemma = raw.get("direct_stream_gemma", {})
    qwen = raw.get("direct_stream_qwen")
    gemma_processors = processor_classes(gemma.get("ollama_ps_snapshots", []), GEMMA_MODEL)
    qwen_processors = processor_classes(qwen.get("ollama_ps_snapshots", []), QWEN_MODEL) if isinstance(qwen, dict) else []
    gemma_processor_class = classify_processor(gemma_processors)
    qwen_processor_class = classify_processor(qwen_processors)
    if gemma_processor_class in {"CPU", "partial GPU/CPU"}:
        classification = "B. throughput collapse / CPU or partial GPU offload"
    elif gemma.get("total_visible_chars", 0) == 0 or (
        gemma.get("chunks_captured", 0) >= 64 and gemma.get("visible_text_chars_after_64_chunks", 0) < 20
    ):
        classification = "C. Gemma prompt-template / prefix pathology"
    elif isinstance(qwen, dict) and qwen_processor_class == gemma_processor_class:
        gemma_first = gemma.get("time_to_first_visible_text_ms") or 999999
        qwen_first = qwen.get("time_to_first_visible_text_ms") or 999999
        gemma_chars = gemma.get("visible_text_chars_after_64_chunks") or 0
        qwen_chars = qwen.get("visible_text_chars_after_64_chunks") or 0
        if qwen_first < gemma_first / 2 or qwen_chars > gemma_chars * 2:
            classification = "D. model-specific weakness where qwen3:14b works better"
        else:
            classification = "A. normal long useful generation"
    elif gemma.get("output_characterization") == "useful_visible_text" and gemma_processor_class == "100% GPU":
        classification = "A. normal long useful generation"
    else:
        classification = "E. inconclusive"
    return {
        "current_head": raw.get("current_head"),
        "starting_git_status": raw.get("starting_git_status"),
        "previous_post_reconnect_data_discarded": True,
        "ollama_alive_before_diagnostics": raw.get("ollama_alive_before", {}).get("ok") is True,
        "ollama_startup_required": False,
        "installed_models_relevant": raw.get("installed_models_relevant"),
        "gemma4_12b_it_qat_available": raw.get("gemma_available"),
        "qwen3_14b_available": raw.get("qwen_available"),
        "warmup": raw.get("warmup"),
        "ollama_ps_before_warmup": raw.get("ollama_ps_before_warmup"),
        "ollama_ps_after_warmup": raw.get("ollama_ps_after_warmup"),
        "gemma_processor_class": gemma_processor_class,
        "gemma_direct_stream_metrics": {
            "wall_clock_ms": gemma.get("wall_clock_ms"),
            "time_to_first_chunk_ms": gemma.get("time_to_first_chunk_ms"),
            "time_to_first_visible_text_ms": gemma.get("time_to_first_visible_text_ms"),
            "visible_text_chars_after_64_chunks": gemma.get("visible_text_chars_after_64_chunks"),
            "visible_text_chars_after_512_chunks": gemma.get("visible_text_chars_after_512_chunks"),
            "total_visible_chars": gemma.get("total_visible_chars"),
            "chunks_captured": gemma.get("chunks_captured"),
            "empty_or_whitespace_chunks": gemma.get("empty_or_whitespace_chunks"),
            "stopped_reason": gemma.get("stopped_reason"),
            "output_characterization": gemma.get("output_characterization"),
            "final_metadata": gemma.get("final_metadata"),
        },
        "backend_comparison_results": summarize_backend(raw.get("backend_results", [])),
        "qwen_processor_class": qwen_processor_class if isinstance(qwen, dict) else "unavailable",
        "qwen_direct_stream_metrics": None
        if not isinstance(qwen, dict)
        else {
            "wall_clock_ms": qwen.get("wall_clock_ms"),
            "time_to_first_chunk_ms": qwen.get("time_to_first_chunk_ms"),
            "time_to_first_visible_text_ms": qwen.get("time_to_first_visible_text_ms"),
            "visible_text_chars_after_64_chunks": qwen.get("visible_text_chars_after_64_chunks"),
            "visible_text_chars_after_512_chunks": qwen.get("visible_text_chars_after_512_chunks"),
            "total_visible_chars": qwen.get("total_visible_chars"),
            "chunks_captured": qwen.get("chunks_captured"),
            "empty_or_whitespace_chunks": qwen.get("empty_or_whitespace_chunks"),
            "stopped_reason": qwen.get("stopped_reason"),
            "output_characterization": qwen.get("output_characterization"),
            "final_metadata": qwen.get("final_metadata"),
        },
        "gemma_vs_qwen_verdict": compare_gemma_qwen(gemma, qwen, gemma_processor_class, qwen_processor_class),
        "classification": classification,
        "recommended_next_action": recommended_action(classification),
        "files_changed": [
            "reports/router_policy/1G-B2-F3-LOCAL-RESPONDER-ROOT-CAUSE-RERUN/run_diagnostic.py",
            "reports/router_policy/1G-B2-F3-LOCAL-RESPONDER-ROOT-CAUSE-RERUN/diagnostic_raw.json",
            "reports/router_policy/1G-B2-F3-LOCAL-RESPONDER-ROOT-CAUSE-RERUN/summary.json",
            "reports/router_policy/1G-B2-F3-LOCAL-RESPONDER-ROOT-CAUSE-RERUN/summary.md",
        ],
    }


def summarize_backend(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary = []
    for item in results:
        summary.append(
            {
                "label": item.get("label"),
                "http_status": item.get("http_status"),
                "wall_clock_ms": item.get("wall_clock_ms"),
                "trace_id": item.get("trace_id"),
                "executed": item.get("executed"),
                "reason": item.get("reason"),
                "error_type": item.get("error_type"),
                "decision_summary": item.get("decision_summary"),
                "backend_timing": item.get("backend_timing"),
                "local_responder_timing": item.get("local_responder_timing"),
                "response_char_count_returned": item.get("response_char_count_returned"),
                "response_truncated": item.get("response_truncated"),
            }
        )
    return summary


def compare_gemma_qwen(gemma: dict[str, Any], qwen: Any, gemma_processor: str, qwen_processor: str) -> str:
    if not isinstance(qwen, dict):
        return "qwen3:14b unavailable or not run"
    if gemma_processor != qwen_processor:
        return "processor placement differs; model comparison is not clean"
    gemma_first = gemma.get("time_to_first_visible_text_ms")
    qwen_first = qwen.get("time_to_first_visible_text_ms")
    gemma_chars = gemma.get("visible_text_chars_after_64_chunks")
    qwen_chars = qwen.get("visible_text_chars_after_64_chunks")
    return (
        f"same placement={gemma_processor}; gemma first visible={gemma_first} ms, "
        f"qwen first visible={qwen_first} ms; gemma visible chars after 64={gemma_chars}, "
        f"qwen visible chars after 64={qwen_chars}"
    )


def recommended_action(classification: str) -> list[str]:
    if classification.startswith("B."):
        return [
            "Treat local responder failures as placement/throughput diagnostics first.",
            "Do not tune NUM_PREDICT or timeout until GPU placement/offload is stable and captured.",
        ]
    if classification.startswith("C."):
        return [
            "Investigate Gemma prompt/template behavior with raw streaming evidence.",
            "Compare a simpler prompt prefix before changing backend defaults.",
        ]
    if classification.startswith("D."):
        return [
            "Run a bounded qwen local-sensitive responder evaluation before changing the default model.",
            "Keep A5-R3/router safety unchanged.",
        ]
    if classification.startswith("A."):
        return [
            "If behavior is acceptable, add failure-path timing instrumentation before any timeout/output-budget changes.",
            "Do not set permanent NUM_PREDICT from one run.",
        ]
    return [
        "Repeat diagnostic after ensuring stable Ollama process and no reconnection.",
        "Do not implement runtime changes from inconclusive data.",
    ]


def write_summary_md(summary: dict[str, Any], raw: dict[str, Any]) -> None:
    gemma = summary["gemma_direct_stream_metrics"]
    qwen = summary.get("qwen_direct_stream_metrics")
    lines = [
        "# Local Responder Root-Cause Rerun",
        "",
        "## Scope",
        "",
        f"- current HEAD: `{summary['current_head']}`",
        f"- starting git status: `{summary['starting_git_status'] or 'clean'}`",
        "- previous post-reconnection diagnostic data discarded: yes",
        "- runtime/router/A5-R3 changes: none",
        "- permanent `NUM_PREDICT`/timeout/model changes: none",
        "",
        "## Preflight",
        "",
        f"- Ollama alive before diagnostics: {summary['ollama_alive_before_diagnostics']}",
        f"- Ollama startup required: {summary['ollama_startup_required']}",
        f"- relevant installed models: {', '.join(summary['installed_models_relevant'])}",
        f"- `gemma4:12b-it-qat` available: {summary['gemma4_12b_it_qat_available']}",
        f"- `qwen3:14b` available: {summary['qwen3_14b_available']}",
        f"- warm-up ok: {summary['warmup'].get('ok')}",
        f"- warm-up duration ms: {summary['warmup'].get('duration_ms')}",
        "",
        "## Gemma Direct Streaming",
        "",
        f"- processor class: `{summary['gemma_processor_class']}`",
        f"- wall-clock ms: `{gemma.get('wall_clock_ms')}`",
        f"- time_to_first_chunk_ms: `{gemma.get('time_to_first_chunk_ms')}`",
        f"- time_to_first_visible_text_ms: `{gemma.get('time_to_first_visible_text_ms')}`",
        f"- visible chars after 64 chunks: `{gemma.get('visible_text_chars_after_64_chunks')}`",
        f"- visible chars after 512 chunks: `{gemma.get('visible_text_chars_after_512_chunks')}`",
        f"- total visible chars: `{gemma.get('total_visible_chars')}`",
        f"- empty/whitespace chunks: `{gemma.get('empty_or_whitespace_chunks')}`",
        f"- stopped reason: `{gemma.get('stopped_reason')}`",
        f"- output characterization: `{gemma.get('output_characterization')}`",
        "",
        "## Backend Comparison",
        "",
        "| case | HTTP | executed | reason | error_type | wall ms | responder ms | chars |",
        "|---|---:|---|---|---|---:|---:|---:|",
    ]
    for item in summary["backend_comparison_results"]:
        timing = item.get("backend_timing") if isinstance(item.get("backend_timing"), dict) else {}
        lines.append(
            f"| {item.get('label')} | {item.get('http_status')} | {item.get('executed')} | "
            f"`{item.get('reason')}` | `{item.get('error_type')}` | {item.get('wall_clock_ms')} | "
            f"{timing.get('local_responder_call_duration_ms')} | {item.get('response_char_count_returned')} |"
        )
    lines.extend(["", "## Qwen Direct Streaming", ""])
    if qwen is None:
        lines.append("- `qwen3:14b` unavailable or not run.")
    else:
        lines.extend(
            [
                f"- processor class: `{summary['qwen_processor_class']}`",
                f"- wall-clock ms: `{qwen.get('wall_clock_ms')}`",
                f"- time_to_first_visible_text_ms: `{qwen.get('time_to_first_visible_text_ms')}`",
                f"- visible chars after 64 chunks: `{qwen.get('visible_text_chars_after_64_chunks')}`",
                f"- visible chars after 512 chunks: `{qwen.get('visible_text_chars_after_512_chunks')}`",
                f"- total visible chars: `{qwen.get('total_visible_chars')}`",
                f"- stopped reason: `{qwen.get('stopped_reason')}`",
                f"- output characterization: `{qwen.get('output_characterization')}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Verdict",
            "",
            f"- Gemma vs qwen verdict: {summary['gemma_vs_qwen_verdict']}",
            f"- classification: `{summary['classification']}`",
            "",
            "## Recommended Next Action",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in summary["recommended_next_action"])
    lines.extend(
        [
            "",
            "## Files",
            "",
        ]
    )
    lines.extend(f"- `{item}`" for item in summary["files_changed"])
    lines.extend(
        [
            "",
            "## Checks",
            "",
            "- `git diff --check` pending after report generation.",
            "- `git status --short` pending after report generation.",
        ]
    )
    (REPORT_DIR / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    raw: dict[str, Any] = {
        "created_at": utc_now(),
        "current_head": run_command(["git", "rev-parse", "HEAD"]).get("stdout", "").strip(),
        "starting_git_status": run_command(["git", "status", "--short"]).get("stdout", "").strip(),
        "previous_post_reconnect_data_discarded": True,
    }
    raw["ollama_alive_before"] = ollama_tags()
    raw["ollama_ps_before_warmup"] = capture_ollama_ps("before_warmup")
    raw["ollama_list"] = run_command(["ollama", "list"], timeout=10)
    tags = raw["ollama_alive_before"]
    names = model_names(tags)
    raw["installed_models_relevant"] = [name for name in names if name in {GEMMA_MODEL, QWEN_MODEL}]
    raw["gemma_available"] = GEMMA_MODEL in names
    raw["qwen_available"] = QWEN_MODEL in names
    if not raw["ollama_alive_before"].get("ok"):
        raw["fatal_error"] = "Ollama is not alive; start Ollama manually and rerun."
    elif not raw["gemma_available"]:
        raw["fatal_error"] = f"{GEMMA_MODEL} is not installed; cannot run required diagnostic."
    else:
        raw["warmup"] = warmup_model(GEMMA_MODEL)
        raw["ollama_ps_after_warmup"] = capture_ollama_ps("after_warmup")
        raw["direct_stream_gemma"] = direct_stream_generate(GEMMA_MODEL, PROBLEM_PROMPT, "direct_gemma_problem")
        raw["backend_results"] = backend_local_chat_cases(GEMMA_MODEL)
        if raw["qwen_available"]:
            raw["qwen_warmup"] = warmup_model(QWEN_MODEL)
            raw["direct_stream_qwen"] = direct_stream_generate(QWEN_MODEL, PROBLEM_PROMPT, "direct_qwen_problem")
        else:
            raw["direct_stream_qwen"] = None
    summary = build_summary(raw) if "fatal_error" not in raw else {"fatal_error": raw["fatal_error"], "current_head": raw["current_head"]}
    raw_path = REPORT_DIR / "diagnostic_raw.json"
    summary_path = REPORT_DIR / "summary.json"
    raw_path.write_text(json.dumps(raw, indent=2, sort_keys=True, ensure_ascii=True), encoding="utf-8")
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=True), encoding="utf-8")
    if "fatal_error" not in raw:
        write_summary_md(summary, raw)
    else:
        (REPORT_DIR / "summary.md").write_text(f"# Local Responder Root-Cause Rerun\n\n- fatal: {raw['fatal_error']}\n", encoding="utf-8")
    print(json.dumps({"raw": str(raw_path), "summary": str(summary_path), "classification": summary.get("classification")}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
