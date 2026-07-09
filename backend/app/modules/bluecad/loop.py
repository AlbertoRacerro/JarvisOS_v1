"""Synchronous BLUECAD AI generate/build/validate/repair loop."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.database import open_sqlite_connection
from app.modules.ai.budget import evaluate_ai_status
from app.modules.ai.contracts import AIProviderAdapter
from app.modules.ai.execution import ProviderBinding, resolve_binding, run_ai_task
from app.modules.ai.settings import get_ai_settings
from app.modules.bluecad.evidence import (
    record_fem_static_evidence,
    record_mesh_quality_evidence,
    record_validation_evidence,
)
from app.modules.bluecad.fem_adapter import append_tier3_checks, solve_static_analysis
from app.modules.bluecad.ledger import (
    candidate_work_dir,
    create_candidate_record,
    finish_attempt,
    get_candidate,
    mark_candidate_valid,
    park_candidate,
    register_artifact,
    start_attempt,
    update_candidate_artifacts,
)
from app.modules.bluecad.mesh_adapter import mesh_analysis_spec
from app.modules.bluecad.models import BluecadCandidateCreate, BluecadCandidateRead, BluecadLoopConfig
from app.modules.bluecad.prompts import PROMPT_VERSION, generate_prompt, repair_prompt
from app.modules.bluecad.service import build_geometry_spec
from app.modules.bluecad.spec import SpecValidationError, canonical_json, canonicalize_geometry_spec
from app.modules.events.service import utc_now

_EXTERNAL_ROUTES = {"external:cheap", "external:reasoning"}


def create_bluecad_candidate(
    workspace_id: str,
    payload: BluecadCandidateCreate,
    *,
    adapters: dict[str, AIProviderAdapter] | None = None,
    bindings: dict[str, ProviderBinding] | None = None,
    force_external_allowed: bool = False,
) -> BluecadCandidateRead:
    loop_config = payload.loop_config or BluecadLoopConfig()
    _validate_loop_config(loop_config)
    candidate = create_candidate_record(workspace_id, payload.brief_text, loop_config)

    blocked_reason = None if force_external_allowed else _external_blocked_reason()
    if blocked_reason is not None:
        park_candidate(candidate.id, "budget_blocked", notes=f"external_blocked_reason={blocked_reason}")
        return _require_candidate(workspace_id, candidate.id)

    attempt_no = 0
    last_spec: dict[str, Any] | None = None
    last_report: dict[str, Any] | None = None
    malformed_on_tier = 0
    saw_malformed = False
    saw_build_or_validation_failure = False

    for tier in loop_config.tier_ladder:
        malformed_on_tier = 0
        for _ in range(loop_config.max_attempts_per_tier):
            attempt_no += 1
            prompt = _prompt_for_attempt(payload.brief_text, last_spec, last_report)
            task_kind = "bluecad_cad_generate" if last_spec is None else "bluecad_cad_repair"
            attempt = start_attempt(candidate.id, attempt_no, tier, prompt_version=PROMPT_VERSION)
            outcome = run_ai_task(
                user_prompt=prompt,
                task_kind=task_kind,
                route_class=tier,
                max_output_tokens=loop_config.max_output_tokens,
                adapters=adapters,
                bindings=bindings,
            )
            if outcome.status == "config_error":
                finish_attempt(
                    attempt.id,
                    proposal_ai_job_id=outcome.ledger_id,
                    proposal_outcome="blocked",
                    error_detail={"error_type": outcome.error_type or outcome.status},
                )
                park_candidate(candidate.id, "budget_blocked", notes=f"external_blocked_reason={outcome.error_type or outcome.status}")
                return _require_candidate(workspace_id, candidate.id)
            if outcome.status != "success" or outcome.response is None or outcome.response.text is None:
                finish_attempt(
                    attempt.id,
                    proposal_ai_job_id=outcome.ledger_id,
                    proposal_outcome="provider_error",
                    error_detail={"error_type": outcome.error_type or outcome.status},
                )
                continue

            try:
                spec = parse_geometry_spec_response(outcome.response.text)
            except SpecValidationError as exc:
                saw_malformed = True
                malformed_on_tier += 1
                finish_attempt(
                    attempt.id,
                    proposal_ai_job_id=outcome.ledger_id,
                    proposal_outcome="malformed",
                    error_detail={"parse_error": exc.detail},
                )
                if malformed_on_tier >= loop_config.max_attempts_per_tier:
                    break
                continue

            malformed_on_tier = 0
            last_spec = spec
            build = _build_and_register(workspace_id, candidate.id, attempt_no, spec)
            verdict = "pass" if build["report"].get("verdict") == "pass" else "fail"
            build_outcome = "ok" if build["result"].verdict != "error" else _build_error_code(build["result"].errors)
            finish_attempt(
                attempt.id,
                proposal_ai_job_id=outcome.ledger_id,
                proposal_outcome="ok",
                build_outcome=build_outcome,
                validation_verdict=verdict,
                spec_artifact_id=build["spec_artifact_id"],
                report_artifact_id=build["report_artifact_id"],
                manifest_artifact_id=build["manifest_artifact_id"],
                error_detail={"prompt_version": PROMPT_VERSION},
            )
            record_validation_evidence(
                workspace_id,
                candidate.id,
                attempt.id,
                build["report"],
                report_artifact_id=build["report_artifact_id"],
            )
            update_candidate_artifacts(
                candidate.id,
                spec_artifact_id=build["spec_artifact_id"],
                glb_artifact_id=build["glb_artifact_id"],
                report_artifact_id=build["report_artifact_id"],
            )
            last_report = build["report"]
            if verdict == "pass":
                mark_candidate_valid(candidate.id)
                _run_simulation_stage(workspace_id, candidate.id, attempt.id, attempt_no, loop_config.analysis_spec, build)
                return _require_candidate(workspace_id, candidate.id)
            saw_build_or_validation_failure = True

    reason = "malformed_repeated" if saw_malformed and not saw_build_or_validation_failure else "attempts_exhausted"
    park_candidate(candidate.id, reason)
    return _require_candidate(workspace_id, candidate.id)


def _run_simulation_stage(
    workspace_id: str,
    candidate_id: str,
    attempt_id: str,
    attempt_no: int,
    analysis_spec_without_geometry: dict[str, Any] | None,
    build: dict[str, Any],
) -> None:
    if analysis_spec_without_geometry is None:
        return
    try:
        out_dir = candidate_work_dir(workspace_id, candidate_id, attempt_no) / "simulation"
        out_dir.mkdir(parents=True, exist_ok=True)
        analysis_spec = _analysis_spec_with_geometry(analysis_spec_without_geometry, build)
        source_run_id = _create_simulation_run(workspace_id, candidate_id, attempt_id, analysis_spec)
    except Exception:
        return
    source_ref = f"bluecad_candidate:{candidate_id}:attempt:{attempt_no}:sim:{source_run_id}"
    try:
        mesh_result = mesh_analysis_spec(analysis_spec, out_dir / "mesh")
    except Exception as exc:  # noqa: BLE001 - sim failures are advisory evidence only.
        mesh_result = _mesh_error_result(exc, analysis_spec)
    try:
        mesh_report_artifact_id = _register_sim_report(workspace_id, out_dir / "mesh_result.json", mesh_result, source_ref)
        record_mesh_quality_evidence(
            workspace_id,
            mesh_result,
            source_run_id=source_run_id,
            report_artifact_id=mesh_report_artifact_id,
            candidate_id=candidate_id,
            attempt_id=attempt_id,
        )
    except Exception:
        return
    if mesh_result.get("verdict") != "pass" or "mesh_inp" not in mesh_result.get("artifacts", {}):
        return
    try:
        fem_summary = solve_static_analysis(analysis_spec, mesh_result, out_dir / "fem")
    except Exception as exc:  # noqa: BLE001 - sim failures are advisory evidence only.
        fem_summary = _fem_error_result(exc)
    fem_report = None
    if fem_summary.get("verdict") == "pass" and analysis_spec.get("pass_criteria"):
        try:
            fem_report = append_tier3_checks({"verdict": "pass", "checks": [], "errors": []}, fem_summary, analysis_spec["pass_criteria"])
        except Exception as exc:  # noqa: BLE001 - Tier 3 failures are advisory evidence only.
            fem_report = {"verdict": "error", "checks": [], "errors": [{"code": "TIER3_ERROR", "detail": {"message": str(exc), "type": type(exc).__name__}}]}
    fem_payload = {"result_summary": fem_summary, "report": fem_report}
    try:
        fem_report_artifact_id = _register_sim_report(workspace_id, out_dir / "fem_result.json", fem_payload, source_ref)
        record_fem_static_evidence(
            workspace_id,
            fem_summary,
            fem_report,
            source_run_id=source_run_id,
            report_artifact_id=fem_report_artifact_id,
            candidate_id=candidate_id,
            attempt_id=attempt_id,
        )
    except Exception:
        return


def _analysis_spec_with_geometry(analysis_spec_without_geometry: dict[str, Any], build: dict[str, Any]) -> dict[str, Any]:
    result = build["result"]
    step_path = result.out_dir / "model.step"
    manifest_path = result.manifest_path
    if manifest_path is None:
        raise RuntimeError("validated BLUECAD build missing manifest for simulation")
    return {**analysis_spec_without_geometry, "geometry": {"step_path": str(step_path), "manifest_path": str(manifest_path)}}


def _register_sim_report(workspace_id: str, path: Path, payload: dict[str, Any], source_ref: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return register_artifact(workspace_id, path, role="bluecad_sim_report", source_ref=source_ref)


def _create_simulation_run(workspace_id: str, candidate_id: str, attempt_id: str, analysis_spec: dict[str, Any]) -> str:
    from uuid import uuid4

    run_id = str(uuid4())
    now = utc_now()
    with open_sqlite_connection() as connection:
        connection.execute(
            """
            INSERT INTO simulation_runs (
                id, workspace_id, model_version_id, run_label, status,
                input_payload, parameter_payload, output_payload, started_at,
                completed_at, created_at, notes
            ) VALUES (?, ?, NULL, ?, 'completed', ?, ?, NULL, ?, ?, ?, ?)
            """,
            (
                run_id,
                workspace_id,
                f"bluecad_attempt_{attempt_id}",
                json.dumps({"candidate_id": candidate_id, "attempt_id": attempt_id}, sort_keys=True),
                json.dumps(analysis_spec, sort_keys=True),
                now,
                now,
                now,
                "BLUECAD advisory synchronous mesh/FEM stage.",
            ),
        )
        connection.commit()
    return run_id


def _mesh_error_result(exc: Exception, analysis_spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "bluecad_mesh_result_v0_1",
        "verdict": "error",
        "errors": [{"code": "MESH_ERROR", "detail": {"message": str(exc), "type": type(exc).__name__}}],
        "attempts": [{"attempt_no": 1, "target_size": analysis_spec.get("mesh", {}).get("target_size"), "counts": {}, "errors": []}],
        "artifacts": {},
    }


def _fem_error_result(exc: Exception) -> dict[str, Any]:
    return {
        "schema_version": "bluecad_result_summary_v0_1",
        "verdict": "error",
        "errors": [{"code": "SOLVE_ERROR", "detail": {"message": str(exc), "type": type(exc).__name__}}],
        "solver": {"tool_id": "calculix", "version": None, "returncode": None},
        "artifacts": {},
    }


def parse_geometry_spec_response(text: str) -> dict[str, Any]:
    payload = _extract_single_json_object(text)
    try:
        loaded = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise SpecValidationError({"message": "LLM response did not contain valid JSON.", "position": exc.pos}) from exc
    try:
        return canonicalize_geometry_spec(loaded)
    except SpecValidationError:
        raise
    except Exception as exc:
        raise SpecValidationError({"message": str(exc), "type": type(exc).__name__}) from exc


def _extract_single_json_object(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].strip() == "```":
            stripped = "\n".join(lines[1:-1]).strip()
    start = stripped.find("{")
    if start < 0:
        raise SpecValidationError({"message": "LLM response must contain one JSON object."})
    depth = 0
    in_string = False
    escape = False
    end = None
    for index, char in enumerate(stripped[start:], start=start):
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                end = index + 1
                break
            if depth < 0:
                break
    if end is None:
        raise SpecValidationError({"message": "LLM response JSON object was incomplete."})
    before = stripped[:start].strip()
    after = stripped[end:].strip()
    if before or after:
        raise SpecValidationError({"message": "LLM response must contain exactly one JSON object."})
    return stripped[start:end]


def _prompt_for_attempt(brief_text: str, last_spec: dict[str, Any] | None, last_report: dict[str, Any] | None) -> str:
    if last_spec is None or last_report is None:
        return generate_prompt(brief_text)
    return repair_prompt(last_spec, last_report)


def _build_and_register(workspace_id: str, candidate_id: str, attempt_no: int, spec: dict[str, Any]) -> dict[str, Any]:
    out_dir = candidate_work_dir(workspace_id, candidate_id, attempt_no)
    out_dir.mkdir(parents=True, exist_ok=True)
    spec_path = out_dir / "geometry_spec.json"
    spec_path.write_text(canonical_json(spec) + "\n", encoding="utf-8")
    result = build_geometry_spec(spec, out_dir)
    source_ref = f"bluecad_candidate:{candidate_id}:attempt:{attempt_no}"
    spec_artifact_id = register_artifact(workspace_id, spec_path, role="bluecad_spec", source_ref=source_ref)
    report_artifact_id = register_artifact(workspace_id, _require_path(result.report_path, out_dir / "validation_report.json"), role="bluecad_report", source_ref=source_ref)
    manifest_artifact_id = None
    glb_artifact_id = None
    if result.manifest_path is not None and result.manifest_path.exists():
        manifest_artifact_id = register_artifact(workspace_id, result.manifest_path, role="bluecad_manifest", source_ref=source_ref)
    glb_path = out_dir / "model.glb"
    if glb_path.exists():
        glb_artifact_id = register_artifact(workspace_id, glb_path, role="bluecad_glb", source_ref=source_ref)
    return {
        "result": result,
        "report": result.report,
        "spec_artifact_id": spec_artifact_id,
        "report_artifact_id": report_artifact_id,
        "manifest_artifact_id": manifest_artifact_id,
        "glb_artifact_id": glb_artifact_id,
    }


def _require_path(path: Path | None, fallback: Path) -> Path:
    resolved = path or fallback
    if not resolved.exists():
        raise RuntimeError(f"expected BLUECAD artifact missing: {resolved}")
    return resolved


def _build_error_code(errors: list[dict[str, Any]]) -> str:
    if not errors:
        return "error"
    code = errors[0].get("code")
    return str(code or "error")


def _external_blocked_reason(route_class: str = "external:cheap") -> str | None:
    binding, _decision = resolve_binding(route_class)
    provider_mode = binding.provider_id if binding is not None else route_class
    status = evaluate_ai_status(get_ai_settings(), provider_mode)
    if status.external_calls_allowed:
        return None
    return status.blocking_reason or "external_calls_blocked"


def _validate_loop_config(loop_config: BluecadLoopConfig) -> None:
    if not loop_config.tier_ladder:
        raise ValueError("tier_ladder must not be empty")
    for route_class in loop_config.tier_ladder:
        if route_class not in _EXTERNAL_ROUTES:
            raise ValueError("BLUECAD loop route classes must be explicit external tiers")


def _require_candidate(workspace_id: str, candidate_id: str) -> BluecadCandidateRead:
    candidate = get_candidate(workspace_id, candidate_id)
    if candidate is None:  # pragma: no cover - defensive persistence guard
        raise RuntimeError("BLUECAD candidate disappeared during loop")
    return candidate
