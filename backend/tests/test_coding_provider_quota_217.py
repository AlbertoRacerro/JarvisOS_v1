"""Spec 217: read-only provider quota rings for Coding → Runtime (offline)."""
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.coding import provider_quota as pq
from app.modules.coding import runtime_routes
from app.modules.coding.runtime_truth import CANONICAL_RUNTIME_REPOSITORY

NOW = datetime(2026, 10, 24, 12, 0, tzinfo=UTC)


def iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def reading(agy: Any = None, **agents: Any) -> dict[str, Any]:
    return {"relay": {"agents": [{"agent_key": key, **body} for key, body in agents.items()]}, "agy": agy}


AGY = {"type": "command", "command": {"name": "quota", "data": {"groups": [
    {"name": "Gemini Models", "buckets": [
        {"id": "gemini-5h", "remaining_fraction": 1.0, "reset_time": "2026-10-24T16:00:00Z", "disabled": False},
        {"id": "gemini-weekly", "remaining_fraction": 0.49, "reset_time": "2026-10-25T22:00:00Z", "disabled": False}]},
    {"name": "Claude and GPT models", "buckets": [
        {"id": "3p-5h", "remaining_fraction": 1.0, "reset_time": "2026-10-24T16:00:00Z", "disabled": False},
        {"id": "3p-weekly", "remaining_fraction": 1.0, "reset_time": "2026-10-28T00:00:00Z", "disabled": True}]},
    {"name": "Gemini 4 Argon", "buckets": [
        {"id": "argon-weekly", "remaining_fraction": 0.49, "reset_time": "2026-10-25T22:00:00Z"}]}]}}}


def provider(payload: dict[str, Any], key: str) -> dict[str, Any]:
    return next(item for item in payload["providers"] if item["provider"] == key)


def test_five_hour_weekly_and_model_pool_windows_are_normalised() -> None:
    payload = pq.normalize(reading(claude={"status": "ok", "as_of": iso(NOW - timedelta(minutes=2)), "windows": [
        {"id": "five_hour", "used_percent": 51, "resets_at": iso(NOW + timedelta(hours=2))},
        {"id": "seven_day", "used_percent": 12.34, "resets_at": iso(NOW + timedelta(days=3))},
        {"id": "seven_day_opus", "label": "Opus weekly", "used_percent": 80, "resets_at": iso(NOW + timedelta(days=3))},
    ]}), NOW)
    claude = provider(payload, "claude")
    assert claude["status"] == "ok"
    kinds = [(w["kind"], w["used_percent"], w["remaining_percent"]) for w in claude["windows"]]
    assert kinds == [("five_hour", 51.0, 49.0), ("weekly", 12.3, 87.7), ("frontier", 80.0, 20.0)]
    assert claude["windows"][2]["label"] == "Opus weekly"
    assert not any(w["stale"] or w["exhausted"] for w in claude["windows"])


def test_window_minutes_win_over_ids() -> None:
    assert pq.window_kind({"id": "primary", "window_minutes": 10080}) == "weekly"
    assert pq.window_kind({"id": "x", "window_minutes": 300}) == "five_hour"
    assert pq.window_kind({"id": "secondary"}) == "weekly"


def test_exhausted_stale_and_past_reset() -> None:
    payload = pq.normalize(reading(codex={"status": "ok", "as_of": iso(NOW - timedelta(hours=3)), "windows": [
        {"id": "primary", "used_percent": 100, "resets_at": iso(NOW + timedelta(minutes=40))},
        {"id": "secondary", "used_percent": 100, "resets_at": iso(NOW - timedelta(hours=1))},
    ]}), NOW)
    five, week = provider(payload, "codex")["windows"]
    assert five["exhausted"] and five["stale"]  # old reading
    assert week["stale"] and not week["exhausted"]  # reset already passed: the 100 % is out of date


@pytest.mark.parametrize("windows", [None, [], [{}], [{"id": "s", "used_percent": "50"}], [{"id": "s", "used_percent": True}],
                                     [{"id": "s", "used_percent": 140}], [{"id": "s", "used_percent": -1}]])
def test_unusable_windows_are_not_rendered_as_zero(windows: Any) -> None:
    claude = provider(pq.normalize(reading(claude={"status": "ok", "as_of": iso(NOW), "windows": windows}), NOW), "claude")
    assert claude["status"] == "unavailable" and claude["windows"] == []


def test_unauthenticated_missing_and_unreadable_states() -> None:
    payload = pq.normalize(reading(claude={"status": "not_logged_in"}), NOW)
    assert provider(payload, "claude")["status"] == "unauthenticated"
    assert provider(payload, "codex") == {"provider": "codex", "label": "Codex (ChatGPT)", "source": "agent-relay limits",
                                         "status": "unavailable", "reason": "no_reading", "windows": []}
    unreadable = pq.normalize({"relay": None, "agy": None}, NOW)
    assert {p["reason"] for p in unreadable["providers"]} == {"relay_limits_unreadable", "agy_quota_unreadable"}


def test_antigravity_buckets_from_agy_quota() -> None:
    agy = provider(pq.normalize(reading(AGY), NOW), "antigravity")
    assert agy["status"] == "ok" and agy["source"] == "agy /quota" and agy["as_of"] == iso(NOW)
    rows = [(w["id"], w["kind"], w["label"], w["remaining_percent"]) for w in agy["windows"]]
    # The Claude & GPT (3p) pool is never shown; Argon is the frontier-model row.
    assert rows == [("gemini-5h", "five_hour", None, 100.0), ("gemini-weekly", "weekly", None, 49.0),
                    ("argon-weekly", "frontier", "Argon · weekly", 49.0)]


def test_antigravity_is_never_estimated() -> None:
    unreadable = provider(pq.normalize(reading(None), NOW), "antigravity")
    assert unreadable["status"] == "unavailable" and unreadable["reason"] == "agy_quota_unreadable" and unreadable["windows"] == []
    junk = {"command": {"data": {"groups": [{"buckets": [{"id": "gemini-5h", "remaining_fraction": 1.4},
                                                          {"id": "gemini-weekly", "remaining_fraction": "0.5"}]}]}}}
    empty = provider(pq.normalize(reading(junk), NOW), "antigravity")
    assert empty["status"] == "unavailable" and empty["reason"] == "no_usage_windows"


def test_agy_output_with_log_lines_before_the_json() -> None:
    assert pq._json_document("warming up\n" + json.dumps(AGY)) == AGY
    assert pq._json_document("no json here") is None


def test_no_tool_text_paths_or_secrets_reach_the_payload() -> None:
    secret = "ghp_" + "a" * 36
    payload = pq.normalize(reading(claude={"status": "ok", "as_of": iso(NOW), "stderr": secret, "path": "/home/x/.config",
                                           "windows": [{"id": secret, "label": "/home/x/secret", "used_percent": 5, "raw": secret}]}), NOW)
    text = json.dumps(payload)
    assert secret not in text and "/home/" not in text
    assert provider(payload, "claude")["windows"][0]["id"] == "window"


def test_cache_reads_once_per_ttl(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JARVISOS_PROVIDER_QUOTA_TTL_S", "600")
    calls: list[int] = []
    clock = [NOW]

    def reader() -> dict[str, Any]:
        calls.append(1)
        return reading(claude={"status": "ok", "as_of": iso(clock[0]), "windows": [{"id": "five_hour", "used_percent": 10}]})

    cache = pq.QuotaCache(reader, clock=lambda: clock[0])
    first = cache.get()
    clock[0] = NOW + timedelta(minutes=5)
    assert cache.get()["read_at"] == first["read_at"] and len(calls) == 1
    clock[0] = NOW + timedelta(minutes=11)
    assert cache.get()["read_at"] == iso(clock[0]) and len(calls) == 2
    assert first["next_read_at"] == iso(NOW + timedelta(minutes=10))


def test_ttl_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JARVISOS_PROVIDER_QUOTA_TTL_S", "3")
    assert pq.ttl_seconds() == pq.MIN_TTL_S
    monkeypatch.setenv("JARVISOS_PROVIDER_QUOTA_TTL_S", "nope")
    assert pq.ttl_seconds() == pq.DEFAULT_TTL_S


def test_missing_tools_are_unreadable_not_an_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JARVISOS_AGENT_RELAY_BIN", "/nonexistent/agent-relay")
    monkeypatch.setenv("JARVISOS_AGY_BIN", "/nonexistent/agy")
    assert pq.read_all() == {"relay": None, "agy": None}


def test_route_requires_the_runtime_repository(monkeypatch: pytest.MonkeyPatch) -> None:
    app = FastAPI()
    app.include_router(runtime_routes.router)
    monkeypatch.setattr(pq, "_cache", pq.QuotaCache(lambda: {}, clock=lambda: NOW))
    client = TestClient(app)
    prefix = runtime_routes.router.prefix
    ok = client.get(f"{prefix}/provider-quotas", params={"repository": CANONICAL_RUNTIME_REPOSITORY})
    assert ok.status_code == 200 and [p["provider"] for p in ok.json()["providers"]] == ["claude", "codex", "antigravity"]
    assert client.get(f"{prefix}/provider-quotas", params={"repository": "someone/else"}).status_code == 400


# Shapes captured from the maintainer's host on 2026-10-24 (agent-relay limits, agy 1.4 `/quota`); free text trimmed.
REAL_RELAY = {"command": "limits", "agents": [
    {"agent_key": "claude", "display_name": "Claude Code", "status": "ok", "plan": None, "reason": None,
     "as_of": "2026-10-24T13:39:36.058877+00:00", "windows": [
         {"id": "session", "label": "5-hour limit", "used_percent": 6.0, "resets_at": "2026-10-24T17:20:00.001189+00:00"},
         {"id": "weekly", "label": "Weekly limit", "used_percent": 80.0, "resets_at": "2026-10-26T06:00:00.001234+00:00"}]},
    {"agent_key": "codex", "display_name": "Codex", "status": "ok", "plan": "plus", "reason": None,
     "as_of": "2026-10-22T14:16:38.267Z", "windows": [
         {"id": "session", "label": "5-hour limit", "used_percent": 4.0, "resets_at": "2026-10-22T17:37:26+00:00"},
         {"id": "weekly", "label": "Weekly limit", "used_percent": 88.0, "resets_at": "2026-10-27T07:45:12+00:00"}]}]}
REAL_AGY = "\n" + json.dumps({"conversation_id": "", "status": "SUCCESS", "num_turns": 0, "command": {"name": "usage", "data": {"groups": [
    {"name": "Gemini Models", "buckets": [
        {"id": "gemini-weekly", "name": "Weekly Limit Remaining", "window": "weekly", "remaining_fraction": 1,
         "reset_time": "2026-10-31T13:39:53Z"},
        {"id": "gemini-5h", "name": "Five Hour Limit Remaining", "window": "5h", "remaining_fraction": 1,
         "reset_time": "2026-10-24T18:39:53Z"}]},
    {"name": "Claude and GPT models", "buckets": [
        {"id": "3p-weekly", "window": "weekly", "remaining_fraction": 1, "reset_time": "2026-10-31T13:39:53Z"},
        {"id": "3p-5h", "window": "5h", "remaining_fraction": 1, "reset_time": "2026-10-24T18:39:53Z"}]},
    {"name": "Gemini 4 Argon", "buckets": [
        {"id": "gemini-argon-wtu-weekly", "name": "Gemini 4 Argon Weekly Limit", "window": "weekly",
         "remaining_fraction": 0.4909217357635498, "reset_time": "2026-10-25T07:58:48Z"}]}]}}})


def test_real_host_readings_map_to_the_expected_rings() -> None:
    now = datetime(2026, 10, 24, 13, 40, tzinfo=UTC)
    payload = pq.normalize({"relay": REAL_RELAY, "agy": pq._json_document(REAL_AGY)}, now)
    rows = {p["provider"]: [(w["kind"], w["remaining_percent"], w["stale"]) for w in p["windows"]] for p in payload["providers"]}
    assert rows["claude"] == [("five_hour", 94.0, False), ("weekly", 20.0, False)]
    # Relay's Codex reading was two days old on the host: shown, but flagged out of date.
    assert rows["codex"] == [("five_hour", 96.0, True), ("weekly", 12.0, True)]
    assert rows["antigravity"] == [("weekly", 100.0, False), ("five_hour", 100.0, False), ("frontier", 49.1, False)]
