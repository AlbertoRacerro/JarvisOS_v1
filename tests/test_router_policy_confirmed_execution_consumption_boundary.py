from __future__ import annotations

import copy
import inspect
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import router_policy_canonical_digest as digest_helper  # noqa: E402
import router_policy_semantic_validator as validator  # noqa: E402


NOW = "2026-06-24T08:30:00+00:00"


def base_confirmation_payload() -> dict:
    return {
        "scope": "external_provider_call",
        "target": "external:scientific_medium",
        "payload_preview": "Redacted summary for provider preflight.",
        "payload_preview_truncated": False,
        "full_payload_available_for_review": True,
        "payload_digest": "sha256:" + "1" * 64,
        "full_payload_digest": "sha256:" + "2" * 64,
        "redaction_status": "redacted",
        "estimated_tokens": 800,
        "estimated_cost_class": "medium",
        "side_effect_level": "high",
        "reversibility": "partially_reversible",
        "diff_summary": None,
        "full_diff_available_for_review": False,
        "full_diff_digest": None,
        "file_operations": [],
        "command": None,
        "cwd": None,
        "terminal_risk_summary": None,
        "env_preview_redacted": None,
        "network_access_expected": True,
        "writes_outside_workspace": False,
        "destructive_command_detected": False,
        "file_paths": [],
    }


def awaiting_confirmation_decision() -> dict:
    decision = {
        "decision_id": "decision-awaiting-001",
        "input_digest": "sha256:" + "3" * 64,
        "created_at": "2026-06-24T08:00:00+00:00",
        "expires_at": "2026-06-24T09:00:00+00:00",
        "lifecycle_stage": "awaiting_confirmation",
        "route_action": "ask_user_confirm",
        "route_tier": "USER_CONFIRM",
        "budget_class": "medium",
        "provider_candidate": "external:scientific_medium",
        "max_tokens_allowed": 1200,
        "dry_run_required": True,
        "allowed_execution_mode": "execute_after_confirm",
        "proposed_external_target": "external:scientific_medium",
        "provider_call_allowed_now": False,
        "external_network_allowed_now": False,
        "confirmation_required": True,
        "confirmation_payload_required": True,
        "confirmation_payload": base_confirmation_payload(),
        "confirmation_options": ["allow_once", "deny", "view_details"],
        "requires_new_decision_after_confirmation": True,
    }
    decision["confirmation_digest"] = digest_helper.compute_confirmation_digest(decision)["digest"]
    return decision


def confirmed_execution_decision(previous: dict, *, consent_id: str = "consent-alpha-001") -> dict:
    return {
        "decision_id": "decision-confirmed-001",
        "input_digest": previous["input_digest"],
        "created_at": "2026-06-24T08:10:00+00:00",
        "expires_at": "2026-06-24T08:50:00+00:00",
        "lifecycle_stage": "confirmed_execution",
        "route_action": "route_external_candidate",
        "route_tier": "SCIENTIFIC_MEDIUM",
        "provider_candidate": "external:frontier",
        "budget_class": "expensive",
        "max_tokens_allowed": 999999,
        "dry_run_required": False,
        "allowed_execution_mode": "execute_after_confirm",
        "proposed_external_target": "external:scientific_medium",
        "provider_call_allowed_now": False,
        "external_network_allowed_now": False,
        "confirmation_required": False,
        "confirmation_payload_required": False,
        "confirmation_payload": None,
        "confirmation_digest": None,
        "confirmation_options": [],
        "consent_context": {
            "consent_id": consent_id,
            "confirmed_previous_decision_id": previous["decision_id"],
            "confirmed_confirmation_digest": previous["confirmation_digest"],
            "confirmation_action": "allow_once",
            "confirmed_at": "2026-06-24T08:10:00+00:00",
        },
    }


def consume(current: dict, previous: dict | None, ledger_path: Path, *, now: str | None = NOW) -> dict:
    return validator.evaluate_confirmed_execution_consumption_boundary(
        current,
        previous,
        now=now,
        ledger_path=ledger_path,
    )


def read_records(ledger_path: Path) -> list[dict]:
    return [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()]


def codes(result: dict) -> set[str]:
    return {violation["code"] for violation in result["violations"]}


def test_valid_activation_consumes_once(tmp_path: Path):
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    ledger = tmp_path / "consumption.jsonl"

    result = consume(current, previous, ledger)

    assert result["consumption_allowed"] is True
    assert result["consumption_key"] == "consent-alpha-001"
    assert result["activation_safe"] is True
    assert result["economic_envelope_complete"] is True
    assert result["automatic_execution_eligible"] is True
    records = read_records(ledger)
    assert len(records) == 1
    assert records[0]["consumption_key"] == "consent-alpha-001"


def test_second_use_of_same_consent_id_fails(tmp_path: Path):
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    ledger = tmp_path / "consumption.jsonl"

    assert consume(current, previous, ledger)["consumption_allowed"] is True
    second = consume(current, previous, ledger)

    assert second["consumption_allowed"] is False
    assert "CONFIRMATION_ALREADY_CONSUMED" in codes(second)
    assert len(read_records(ledger)) == 1


def test_a5_activation_failure_does_not_write_ledger_record(tmp_path: Path):
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    current["input_digest"] = "sha256:" + "4" * 64
    ledger = tmp_path / "consumption.jsonl"

    result = consume(current, previous, ledger)

    assert result["consumption_allowed"] is False
    assert result["activation_safe"] is False
    assert "STALE_CONFIRMATION_DECISION" in codes(result)
    assert not ledger.exists()


def test_missing_empty_too_short_non_string_and_placeholder_consent_id_fail_closed(tmp_path: Path):
    previous = awaiting_confirmation_decision()
    cases = [
        ("missing", None),
        ("empty", ""),
        ("too-short", "short"),
        ("non-string", 12345),
        ("placeholder", "test"),
    ]

    for name, consent_id in cases:
        current = confirmed_execution_decision(previous)
        if name == "missing":
            current["consent_context"].pop("consent_id")
        else:
            current["consent_context"]["consent_id"] = consent_id
        ledger = tmp_path / f"{name}.jsonl"

        result = consume(current, previous, ledger)

        assert result["consumption_allowed"] is False
        assert "CONSENT_ID_INVALID" in codes(result)
        assert not ledger.exists()


def test_consent_id_does_not_require_uuid_only(tmp_path: Path):
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous, consent_id="ticket-for-review-42")

    result = consume(current, previous, tmp_path / "consumption.jsonl")

    assert result["consumption_allowed"] is True
    assert result["consumption_key"] == "ticket-for-review-42"


def test_confirmed_digest_mismatch_fails_through_a5_a4_and_does_not_consume(tmp_path: Path):
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    current["consent_context"]["confirmed_confirmation_digest"] = "sha256:" + "9" * 64
    ledger = tmp_path / "consumption.jsonl"

    result = consume(current, previous, ledger)

    assert result["consumption_allowed"] is False
    assert result["activation_safe"] is False
    assert "CONSENT_DIGEST_MISMATCH" in codes(result)
    assert not ledger.exists()


def test_previous_decision_id_mismatch_fails_through_a5_a4_and_does_not_consume(tmp_path: Path):
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    current["consent_context"]["confirmed_previous_decision_id"] = "different-decision"
    ledger = tmp_path / "consumption.jsonl"

    result = consume(current, previous, ledger)

    assert result["consumption_allowed"] is False
    assert result["activation_safe"] is False
    assert "CONSENT_CONTEXT_MISSING" in codes(result)
    assert not ledger.exists()


def test_missing_or_invalid_now_fails_closed_and_does_not_consume(tmp_path: Path):
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)

    missing = consume(current, previous, tmp_path / "missing.jsonl", now=None)
    invalid = consume(current, previous, tmp_path / "invalid.jsonl", now="not-a-time")

    assert missing["consumption_allowed"] is False
    assert invalid["consumption_allowed"] is False
    assert "STALE_CONFIRMATION_DECISION" in codes(missing)
    assert "STALE_CONFIRMATION_DECISION" in codes(invalid)
    assert not (tmp_path / "missing.jsonl").exists()
    assert not (tmp_path / "invalid.jsonl").exists()


def test_ledger_read_failure_fails_closed(tmp_path: Path):
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    ledger_dir = tmp_path / "directory_instead_of_file"
    ledger_dir.mkdir()

    result = consume(current, previous, ledger_dir)

    assert result["consumption_allowed"] is False
    assert "CONFIRMATION_CONSUMPTION_LEDGER_READ_FAILED" in codes(result)


def test_ledger_write_failure_fails_closed(tmp_path: Path):
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    parent_file = tmp_path / "not_a_directory"
    parent_file.write_text("blocks mkdir", encoding="utf-8")
    ledger = parent_file / "consumption.jsonl"

    result = consume(current, previous, ledger)

    assert result["consumption_allowed"] is False
    assert "CONFIRMATION_CONSUMPTION_LEDGER_WRITE_FAILED" in codes(result)


def test_corrupt_ledger_line_fails_closed(tmp_path: Path):
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    ledger = tmp_path / "consumption.jsonl"
    ledger.write_text("{not-json}\n", encoding="utf-8")

    result = consume(current, previous, ledger)

    assert result["consumption_allowed"] is False
    assert "CONFIRMATION_CONSUMPTION_LEDGER_CORRUPT" in codes(result)


def test_partial_ledger_line_fails_closed(tmp_path: Path):
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    ledger = tmp_path / "consumption.jsonl"
    ledger.write_text(json.dumps({"schema_version": "v1", "consumption_key": "abc"}) , encoding="utf-8")

    result = consume(current, previous, ledger)

    assert result["consumption_allowed"] is False
    assert "CONFIRMATION_CONSUMPTION_LEDGER_PARTIAL_LINE" in codes(result)


def test_duplicate_ledger_key_fails_closed(tmp_path: Path):
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    ledger = tmp_path / "consumption.jsonl"
    record = {
        "schema_version": "v1",
        "consumption_key": "duplicate-key",
    }
    ledger.write_text(json.dumps(record) + "\n" + json.dumps(record) + "\n", encoding="utf-8")

    result = consume(current, previous, ledger)

    assert result["consumption_allowed"] is False
    assert "CONFIRMATION_CONSUMPTION_LEDGER_DUPLICATE_KEY" in codes(result)


def test_no_provider_or_external_network_grant(tmp_path: Path):
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)

    result = consume(current, previous, tmp_path / "consumption.jsonl")

    assert result["consumption_allowed"] is True
    assert "provider_call_allowed_now" not in result
    assert "external_network_allowed_now" not in result
    assert "tool_execution_allowed_now" not in result
    assert current["provider_call_allowed_now"] is False
    assert current["external_network_allowed_now"] is False


def test_no_mutation_of_current_or_previous_decision(tmp_path: Path):
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    previous_before = copy.deepcopy(previous)
    current_before = copy.deepcopy(current)

    result = consume(current, previous, tmp_path / "consumption.jsonl")

    assert result["consumption_allowed"] is True
    assert current == current_before
    assert previous == previous_before


def test_ledger_record_contains_schema_version_v1_and_no_prompt_raw_payload_or_secrets(tmp_path: Path):
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)
    ledger = tmp_path / "consumption.jsonl"

    consume(current, previous, ledger)

    record = read_records(ledger)[0]
    serialized = json.dumps(record, sort_keys=True)
    assert record["schema_version"] == "v1"
    assert "prompt" not in serialized.lower()
    assert "raw" not in serialized.lower()
    assert "payload_preview" not in serialized
    assert "provider response" not in serialized.lower()
    assert ".env" not in serialized
    assert "api_key" not in serialized.lower()
    assert "secret" not in serialized.lower()


def test_ledger_economic_envelope_is_sourced_from_previous_decision_not_current(tmp_path: Path):
    previous = awaiting_confirmation_decision()
    previous["provider_candidate"] = "external:cheap"
    previous["budget_class"] = "low"
    previous["max_tokens_allowed"] = 321
    previous["dry_run_required"] = True
    previous["allowed_execution_mode"] = "execute_after_confirm"
    previous["confirmation_digest"] = digest_helper.compute_confirmation_digest(previous)["digest"]
    current = confirmed_execution_decision(previous)
    current["provider_candidate"] = "external:frontier"
    current["budget_class"] = "high"
    current["max_tokens_allowed"] = 999999
    ledger = tmp_path / "consumption.jsonl"

    result = consume(current, previous, ledger)

    assert result["consumption_allowed"] is True
    envelope = read_records(ledger)[0]["economic_envelope"]
    assert envelope["provider_candidate"] == "external:cheap"
    assert envelope["budget_class"] == "low"
    assert envelope["max_tokens_allowed"] == 321
    assert envelope["dry_run_required"] is True
    assert envelope["allowed_execution_mode"] == "execute_after_confirm"


def test_ledger_record_preserves_economic_envelope_when_present(tmp_path: Path):
    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)

    result = consume(current, previous, tmp_path / "consumption.jsonl")

    assert result["economic_envelope_complete"] is True
    envelope = read_records(tmp_path / "consumption.jsonl")[0]["economic_envelope"]
    assert envelope == {
        "route_tier": "USER_CONFIRM",
        "budget_class": "medium",
        "provider_candidate": "external:scientific_medium",
        "max_tokens_allowed": 1200,
        "dry_run_required": True,
        "allowed_execution_mode": "execute_after_confirm",
    }


def test_route_tier_alone_does_not_make_economic_envelope_complete(tmp_path: Path):
    previous = awaiting_confirmation_decision()
    for field in ("budget_class", "provider_candidate", "max_tokens_allowed", "dry_run_required", "allowed_execution_mode"):
        previous.pop(field)
    previous["route_tier"] = "FRONTIER"
    previous["confirmation_digest"] = digest_helper.compute_confirmation_digest(previous)["digest"]
    current = confirmed_execution_decision(previous)

    result = consume(current, previous, tmp_path / "consumption.jsonl")

    assert result["consumption_allowed"] is True
    assert result["economic_envelope_complete"] is False
    assert result["automatic_execution_eligible"] is False
    assert "missing provider_candidate" in result["economic_envelope_limitations"]
    assert read_records(tmp_path / "consumption.jsonl")[0]["economic_envelope"] == {"route_tier": "FRONTIER"}


def test_missing_economic_fields_consume_but_mark_automatic_execution_ineligible(tmp_path: Path):
    previous = awaiting_confirmation_decision()
    previous.pop("allowed_execution_mode")
    previous.pop("max_tokens_allowed")
    previous["confirmation_digest"] = digest_helper.compute_confirmation_digest(previous)["digest"]
    current = confirmed_execution_decision(previous)

    result = consume(current, previous, tmp_path / "consumption.jsonl")

    assert result["consumption_allowed"] is True
    assert result["economic_envelope_complete"] is False
    assert result["automatic_execution_eligible"] is False
    assert "missing allowed_execution_mode" in result["economic_envelope_limitations"]
    assert "missing max_tokens_allowed" in result["economic_envelope_limitations"]
    record = read_records(tmp_path / "consumption.jsonl")[0]
    assert record["automatic_execution_eligible"] is False


def test_invalid_max_tokens_allowed_makes_economic_envelope_incomplete(tmp_path: Path):
    previous = awaiting_confirmation_decision()
    previous["max_tokens_allowed"] = "1200"
    previous["confirmation_digest"] = digest_helper.compute_confirmation_digest(previous)["digest"]
    current = confirmed_execution_decision(previous)

    result = consume(current, previous, tmp_path / "consumption.jsonl")

    assert result["consumption_allowed"] is True
    assert result["economic_envelope_complete"] is False
    assert result["automatic_execution_eligible"] is False
    assert "invalid max_tokens_allowed" in result["economic_envelope_limitations"]


def test_positive_max_tokens_allowed_required_for_economic_envelope_complete(tmp_path: Path):
    for invalid in (0, -1, True):
        previous = awaiting_confirmation_decision()
        previous["max_tokens_allowed"] = invalid
        previous["confirmation_digest"] = digest_helper.compute_confirmation_digest(previous)["digest"]
        current = confirmed_execution_decision(previous, consent_id=f"consent-invalid-{invalid}")

        result = consume(current, previous, tmp_path / f"{invalid}.jsonl")

        assert result["consumption_allowed"] is True
        assert result["economic_envelope_complete"] is False
        assert "invalid max_tokens_allowed" in result["economic_envelope_limitations"]

    previous = awaiting_confirmation_decision()
    current = confirmed_execution_decision(previous)

    valid = consume(current, previous, tmp_path / "valid.jsonl")

    assert valid["consumption_allowed"] is True
    assert valid["economic_envelope_complete"] is True
    assert valid["automatic_execution_eligible"] is True


def test_helper_uses_a5_and_has_no_wall_clock_or_provider_network_calls():
    source = inspect.getsource(validator.evaluate_confirmed_execution_consumption_boundary)
    append_source = inspect.getsource(validator._append_consumption_record)

    assert "evaluate_confirmed_execution_activation_boundary" in source
    assert "datetime.now" not in source
    assert "time.time" not in source
    assert "utcnow(" not in source
    assert "requests" not in source
    assert "httpx" not in source
    assert "openai" not in source
    assert "os.environ" not in source
    assert "os.fsync" in append_source
