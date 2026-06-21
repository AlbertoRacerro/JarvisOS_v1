import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.modules.local_ai.classification.adapter import ClassificationAdapterConfig, ClassificationAdapterResult
from app.modules.local_ai.classification.contracts import ClassificationAttemptDiagnostics, ClassificationFailureCode
from app.modules.local_ai.intake.probe_fast_intake import (
    FAST_INTAKE_SCHEMA_VERSION,
    REPORT_SCHEMA_VERSION,
    BroadStorageBuckets,
    DomainBucket,
    ExplicitMentions,
    FastIntakeSignalForm,
    FastIntakeSuitability,
    ObservableFlags,
    ProjectBucket,
    RecordBucket,
    SensitivityBucket,
    ShortDescription,
    StatusBucket,
    StorageRelevance,
    Uncertainty,
    UncertaintyReason,
    build_fast_intake_prompt,
    build_fast_intake_smoke_report,
    fast_intake_probe_cases,
    parse_fast_intake_output,
    summary_lines,
    write_probe_report,
)


def _diagnostics(
    config: ClassificationAdapterConfig,
    *,
    prompt: str = "",
    raw_content_empty: bool = False,
    thinking_present: bool | None = False,
    done_reason: str | None = "stop",
    fallback_used: bool = False,
    fallback_reason: ClassificationFailureCode | None = None,
) -> ClassificationAttemptDiagnostics:
    return ClassificationAttemptDiagnostics(
        model_name=config.model_name,
        endpoint=config.endpoint_url,
        prompt_chars=len(prompt),
        input_chars=0,
        max_output_tokens=config.max_output_tokens,
        temperature=config.temperature,
        timeout_seconds=config.timeout_seconds,
        latency_ms=10,
        raw_content_empty=raw_content_empty,
        thinking_present=thinking_present,
        done_reason=done_reason,
        schema_valid=False,
        fallback_used=fallback_used,
        fallback_reason=fallback_reason,
    )


def _valid_fast_intake_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": FAST_INTAKE_SCHEMA_VERSION,
        "source": {
            "input_id": "synthetic-1",
            "conversation_id": "synthetic",
            "timestamp": "2026-06-21T00:00:00Z",
            "raw_text_preserved": True,
        },
        "observable_flags": {
            "contains_user_preference": False,
            "contains_user_decision": True,
            "contains_assumption": False,
            "contains_design_constraint": True,
            "contains_open_question": False,
            "contains_action_request": False,
            "contains_test_result": False,
            "contains_numbers_or_metrics": False,
            "mentions_previous_context": False,
            "mentions_project_or_artifact": True,
            "mentions_code_or_command": False,
            "mentions_source_or_literature": False,
        },
        "broad_storage_buckets": {
            "storage_relevance": "high",
            "record_bucket": "decision",
            "project_bucket": "jarvisos",
            "domain_bucket": "memory",
            "sensitivity_bucket": "internal",
            "status_bucket": "proposed",
        },
        "explicit_mentions": {
            "entities": [],
            "projects": ["JarvisOS"],
            "artifacts": [],
            "commits_or_versions": [],
            "numbers_or_metrics": [],
        },
        "short_description": {
            "surface_summary": "Staged memory intake decision.",
            "preserved_user_phrasing": [],
        },
        "uncertainty": {
            "needs_enrichment": True,
            "needs_user_confirmation": False,
            "reason": "important_decision",
        },
        "confidence": {
            "observable": 0.9,
            "bucket_assignment": 0.82,
        },
    }
    payload.update(overrides)
    return payload


class FakeFastIntakeAdapter:
    def __init__(self, config: ClassificationAdapterConfig) -> None:
        self.config = config

    def complete(self, prompt: str, *, input_chars: int = 0) -> ClassificationAdapterResult:
        content = json.dumps(_payload_for_prompt(prompt))
        return ClassificationAdapterResult(
            success=True,
            model_name=self.config.model_name,
            runtime_endpoint=self.config.endpoint_url,
            diagnostics=_diagnostics(self.config, prompt=prompt),
            response_text=content,
        )


class FailingFastIntakeAdapter(FakeFastIntakeAdapter):
    def complete(self, prompt: str, *, input_chars: int = 0) -> ClassificationAdapterResult:
        if self.config.model_name == "qwen3:8b":
            return ClassificationAdapterResult(
                success=False,
                model_name=self.config.model_name,
                runtime_endpoint=self.config.endpoint_url,
                diagnostics=_diagnostics(
                    self.config,
                    prompt=prompt,
                    raw_content_empty=True,
                    done_reason=None,
                    fallback_used=True,
                    fallback_reason=ClassificationFailureCode.timeout,
                ),
                failure_code=ClassificationFailureCode.timeout,
                failure_message="simulated timeout",
            )
        return super().complete(prompt, input_chars=input_chars)


def _payload_for_prompt(prompt: str) -> dict[str, object]:
    source_text = prompt.rsplit("Input:", 1)[-1]
    payload = _valid_fast_intake_payload()
    if "ok grazie" in source_text:
        payload["observable_flags"] = {
            key: False for key in payload["observable_flags"]  # type: ignore[index]
        }
        payload["broad_storage_buckets"] = {
            "storage_relevance": "low",
            "record_bucket": "unknown",
            "project_bucket": "unknown",
            "domain_bucket": "unknown",
            "sensitivity_bucket": "public",
            "status_bucket": "raw",
        }
        payload["explicit_mentions"] = {
            "entities": [],
            "projects": [],
            "artifacts": [],
            "commits_or_versions": [],
            "numbers_or_metrics": [],
        }
        payload["uncertainty"] = {
            "needs_enrichment": False,
            "needs_user_confirmation": False,
            "reason": "none",
        }
    if "API_KEY_PLACEHOLDER_12345" in source_text:
        payload["observable_flags"] = {
            "contains_user_preference": False,
            "contains_user_decision": False,
            "contains_assumption": False,
            "contains_design_constraint": False,
            "contains_open_question": False,
            "contains_action_request": False,
            "contains_test_result": False,
            "contains_numbers_or_metrics": True,
            "mentions_previous_context": False,
            "mentions_project_or_artifact": False,
            "mentions_code_or_command": True,
            "mentions_source_or_literature": False,
        }
        payload["broad_storage_buckets"] = {
            "storage_relevance": "high",
            "record_bucket": "note",
            "project_bucket": "unknown",
            "domain_bucket": "software",
            "sensitivity_bucket": "secret",
            "status_bucket": "raw",
        }
        payload["explicit_mentions"] = {
            "entities": [],
            "projects": [],
            "artifacts": ["API_KEY_PLACEHOLDER_12345"],
            "commits_or_versions": [],
            "numbers_or_metrics": ["12345"],
        }
        payload["uncertainty"] = {
            "needs_enrichment": True,
            "needs_user_confirmation": True,
            "reason": "sensitive",
        }
    return payload


def test_fast_intake_schema_accepts_broad_buckets_and_booleans() -> None:
    form = FastIntakeSignalForm.model_validate(_valid_fast_intake_payload())

    assert form.schema_version == FAST_INTAKE_SCHEMA_VERSION
    assert form.source.raw_text_preserved is True
    assert form.observable_flags.contains_user_decision is True
    assert form.broad_storage_buckets.storage_relevance == StorageRelevance.high
    assert form.broad_storage_buckets.record_bucket == RecordBucket.decision
    assert form.broad_storage_buckets.project_bucket == ProjectBucket.jarvisos
    assert form.broad_storage_buckets.domain_bucket == DomainBucket.memory
    assert form.broad_storage_buckets.sensitivity_bucket == SensitivityBucket.internal
    assert form.broad_storage_buckets.status_bucket == StatusBucket.proposed
    assert form.uncertainty.reason == UncertaintyReason.important_decision


def test_fast_intake_schema_forbids_authorization_fields() -> None:
    payload = _valid_fast_intake_payload(
        tool_authorization="run_tests",
        provider_authorization="deepseek",
        retrieval_authorization=True,
        memory_write_authorization=True,
        route_selection="memory_runtime",
        final_sensitivity_decision="public",
        canonical_memory_promotion=True,
        knowledge_card={"title": "Do not accept"},
    )

    with pytest.raises(ValidationError) as exc:
        FastIntakeSignalForm.model_validate(payload)

    forbidden_locations = {tuple(error["loc"]) for error in exc.value.errors()}
    assert ("tool_authorization",) in forbidden_locations
    assert ("provider_authorization",) in forbidden_locations
    assert ("retrieval_authorization",) in forbidden_locations
    assert ("memory_write_authorization",) in forbidden_locations
    assert ("route_selection",) in forbidden_locations
    assert ("final_sensitivity_decision",) in forbidden_locations
    assert ("canonical_memory_promotion",) in forbidden_locations
    assert ("knowledge_card",) in forbidden_locations


def test_fast_intake_invalid_enum_fails() -> None:
    payload = _valid_fast_intake_payload(
        broad_storage_buckets={
            "storage_relevance": "urgent",
            "record_bucket": "decision",
            "project_bucket": "jarvisos",
            "domain_bucket": "memory",
            "sensitivity_bucket": "internal",
            "status_bucket": "proposed",
        }
    )

    with pytest.raises(ValueError):
        parse_fast_intake_output(json.dumps(payload))


def test_fast_intake_report_omits_raw_case_prompt_messages_and_output(tmp_path: Path) -> None:
    cases = fast_intake_probe_cases()
    report = build_fast_intake_smoke_report(
        installed_model_names=("qwen3:8b", "gemma4:12b-it-qat"),
        adapter_factory=FakeFastIntakeAdapter,
        created_at_utc=datetime(2026, 6, 21, 13, 0, tzinfo=UTC),
    )
    path = write_probe_report(report, tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    lines = summary_lines(report, path)
    serialized = report.model_dump_json()

    assert path.name == "fast_intake_probe_smoke_20260621T130000.json"
    assert payload["schema_version"] == REPORT_SCHEMA_VERSION
    assert report.mode == "smoke"
    assert set(report.candidate_model_names) == {"qwen3:8b", "gemma4:12b-it-qat"}
    assert all(summary.runtime_approved is False for summary in report.profile_summaries)
    assert any("model=qwen3:8b" in line for line in lines)

    for case in cases:
        assert case.case_id in serialized
        assert case.text not in serialized
        assert build_fast_intake_prompt(case) not in serialized
    assert "API_KEY_PLACEHOLDER_12345" not in serialized
    assert "[redacted]" in serialized
    assert "messages" not in serialized
    assert "response_text" not in serialized
    assert "surface_summary" not in serialized
    assert "preserved_user_phrasing" not in serialized


def test_fast_intake_model_failure_does_not_abort_smoke_test() -> None:
    report = build_fast_intake_smoke_report(
        installed_model_names=("qwen3:8b", "gemma4:12b-it-qat"),
        adapter_factory=FailingFastIntakeAdapter,
        created_at_utc=datetime(2026, 6, 21, 13, 15, tzinfo=UTC),
    )
    by_model = {summary.model_name: summary for summary in report.profile_summaries}

    assert by_model["qwen3:8b"].timeout_count == by_model["qwen3:8b"].attempts
    assert by_model["qwen3:8b"].suitability_label == FastIntakeSuitability.rejected
    assert by_model["gemma4:12b-it-qat"].schema_valid_rate == 1
    assert any(result.model_name == "gemma4:12b-it-qat" and result.schema_valid for result in report.results)
    assert any(result.model_name == "qwen3:8b" and result.fallback_used for result in report.results)


def test_fast_intake_profiles_cannot_be_runtime_approved_even_when_candidate() -> None:
    report = build_fast_intake_smoke_report(
        installed_model_names=("gemma4:12b-it-qat",),
        adapter_factory=FakeFastIntakeAdapter,
        created_at_utc=datetime(2026, 6, 21, 13, 30, tzinfo=UTC),
    )

    assert report.profile_summaries
    assert all(summary.runtime_approved is False for summary in report.profile_summaries)
    assert all(result.runtime_approved is False for result in report.results)
    assert not hasattr(report.profile_summaries[0], "memory_write_authorization")
    assert not hasattr(report.profile_summaries[0], "retrieval_authorization")


def test_fast_intake_schema_components_are_broad_not_final_cards() -> None:
    assert set(FastIntakeSignalForm.model_fields) == {
        "schema_version",
        "source",
        "observable_flags",
        "broad_storage_buckets",
        "explicit_mentions",
        "short_description",
        "uncertainty",
        "confidence",
    }
    assert "knowledge_card" not in FastIntakeSignalForm.model_fields
    assert "memory_card" not in FastIntakeSignalForm.model_fields
    assert "decision_card" not in FastIntakeSignalForm.model_fields
    assert BroadStorageBuckets(
        storage_relevance=StorageRelevance.medium,
        record_bucket=RecordBucket.note,
        project_bucket=ProjectBucket.general,
        domain_bucket=DomainBucket.general,
        sensitivity_bucket=SensitivityBucket.internal,
        status_bucket=StatusBucket.raw,
    )
    assert ObservableFlags(**{key: False for key in ObservableFlags.model_fields})
    assert ExplicitMentions()
    assert ShortDescription(surface_summary="", preserved_user_phrasing=())
    assert Uncertainty(needs_enrichment=False, needs_user_confirmation=False, reason=UncertaintyReason.none)
