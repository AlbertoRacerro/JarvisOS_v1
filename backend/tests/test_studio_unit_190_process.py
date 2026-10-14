"""Spec 190: a published Studio process unit in the Process draft and the mixed solve (real 187 sandbox, fake DWSIM)."""

from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app
from app.modules.process_stack import draft, draft_compiler, dynamic_engine, editor, mixed, mixed_runtime, studio_unit
from app.modules.process_stack.draft_models import UNIT_REGISTRY
from app.modules.process_stack.draft_models import (
    AddStream,
    AddUnit,
    Connect,
    DraftQuantity,
    SetStreamCulture,
    SetStreamSpec,
    SetThermo,
    SetUnitParams,
    UpdateStudioUnit,
)
from app.modules.studio_runtime.runtime import status
from tests.plumbing_170_support import codes, find, new_workspace, pbr_document
from tests.studio_unit_190_support import (
    GOLDEN_BODY,
    GOLDEN_CONTRACT,
    MIX_BODY,
    golden_case,
    publish_next_version,
    publish_unit,
)

Q = DraftQuantity


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("JARVISOS_STUDIO_USER_CODE_ENABLED", "1")
    get_settings.cache_clear()
    assert status()["available"], "qualification host must run bubblewrap"
    workspace = new_workspace()
    with TestClient(create_app()) as test_client:
        test_client.workspace = workspace  # type: ignore[attr-defined]
        yield test_client
    get_settings.cache_clear()


def _publish(client, body: str = GOLDEN_BODY) -> tuple[str, str]:
    return publish_unit(client, body, GOLDEN_CONTRACT, workspace=client.workspace, case=golden_case())


def _feed(sid: str, tag: str, x: int, *, flow: float, temperature: float, nitrogen: float, biomass: float = 0.0):
    return [
        AddStream(op="add_stream", id=sid, tag=tag, x=x, y=0),
        SetStreamSpec(op="set_stream_spec", stream=sid, pressure=Q(value=2.0, unit="bar"),
                      temperature=Q(value=temperature, unit="K"), mass_flow=Q(value=flow, unit="kg/s"),
                      composition={"Water": 1.0}, composition_basis="mass"),
        SetStreamCulture(op="set_stream_culture", stream=sid, culture={
            "biomass": Q(value=biomass, unit="kg/m3"), "nitrogen": Q(value=nitrogen, unit="kg/m3"),
            "salinity": Q(value=35.0, unit="g/kg")}),
    ]


def golden_ops(version_id: str, *, split: float = 50.0, heater: bool = True) -> list[Any]:
    ops: list[Any] = [
        SetThermo(op="set_thermo", compounds=["Water"], property_package="NRTL"),
        AddUnit(op="add_unit", id="dosing", type="StudioUnit", tag="Dosing", x=200, y=0, version_id=version_id),
        *_feed("cf", "Culture", 0, flow=0.02, temperature=300.0, nitrogen=0.05, biomass=0.5),
        *_feed("df", "Dose", 0, flow=0.005, temperature=290.0, nitrogen=2.0),
        AddStream(op="add_stream", id="out", tag="Outlet", x=300, y=0),
        AddStream(op="add_stream", id="unused", tag="Unused", x=300, y=50),
        Connect(op="connect", stream="cf", end="target", unit="dosing", port=0),
        Connect(op="connect", stream="df", end="target", unit="dosing", port=1),
        Connect(op="connect", stream="out", end="source", unit="dosing", port=0),
        Connect(op="connect", stream="unused", end="source", unit="dosing", port=1),
        SetUnitParams(op="set_unit_params", unit="dosing", values={"dose_split": Q(value=split, unit="percent")}),
    ]
    if heater:
        ops += [
            AddUnit(op="add_unit", id="heater", type="Heater", tag="Heater", x=400, y=0),
            AddStream(op="add_stream", id="hot", tag="Hot", x=500, y=0),
            Connect(op="connect", stream="out", end="target", unit="heater", port=0),
            Connect(op="connect", stream="hot", end="source", unit="heater", port=0),
            SetUnitParams(op="set_unit_params", unit="heater", mode="outlet_temperature",
                          values={"outlet_temperature": Q(value=310.0, unit="K")}),
        ]
    return ops


def _draft(workspace: str, ops: list[Any]) -> dict[str, Any]:
    state = draft.create_draft(workspace, "studio unit")
    return draft.patch(workspace, state["draft_id"], state["revision"], ops)




# ---------------------------------------------------------------- fake DWSIM (flashes only) over the real mixed runtime


class FakeClient:
    def __enter__(self) -> FakeClient:
        return self

    def __exit__(self, *_exc: object) -> None:
        return None


class Dwsim:
    """Counts every DWSIM contact; the flash is a pure echo of the state it is given."""

    def __init__(self) -> None:
        self.flashes: list[str] = []
        self.clients = 0

    def flash(self, state: dict[str, Any], tag: str, _client: Any, **kwargs: Any) -> dict[str, Any]:
        self.flashes.append(tag)
        spec = kwargs.get("spec")
        if spec is not None:  # an operator feed
            fractions = mixed_runtime._mass_fractions_from_spec(spec, kwargs["compounds"])
            state = {"temperature_K": spec["temperature"]["si"], "pressure_Pa": spec["pressure"]["si"],
                     "mass_flow_kg_s": mixed_runtime._feed_mass_flow(spec, fractions), "mass_fractions": fractions}
        return {"temperature_K": state["temperature_K"], "pressure_Pa": state["pressure_Pa"],
                "mass_flow_kg_s": state["mass_flow_kg_s"], "mass_fractions": dict(state["mass_fractions"]),
                "vapor_fraction": 0.0, "phases": [{"name": "Mixture", "density_kg_m3": 1000.0}]}

    def client(self) -> tuple[FakeClient, str, str]:
        self.clients += 1
        return FakeClient(), "a" * 64, "10.2.9"


@pytest.fixture
def dwsim(monkeypatch):
    fake = Dwsim()
    monkeypatch.setattr(mixed_runtime, "_flash", fake.flash)
    monkeypatch.setattr(editor, "_client", fake.client)
    return fake


def _run(workspace: str, state: dict[str, Any]) -> dict[str, Any]:
    return draft.execute(workspace, state["draft_id"], state["revision"], "run")["run"]


def _patch(workspace: str, state: dict[str, Any], ops: list[Any]) -> dict[str, Any]:
    return draft.patch(workspace, state["draft_id"], state["revision"], ops)


def _assert_balances_closed(run: dict[str, Any]) -> None:
    balances = run["mixed_solve"]["balances"]
    assert {"carrier_mass", "biomass", "nitrogen", "salinity"} <= set(balances), balances
    assert all(item["passed"] for item in balances.values()), balances


def _studio(run: dict[str, Any], tag: str = "Dosing") -> dict[str, Any]:
    return run["units"][tag]["studio"]


# ---------------------------------------------------------------- golden dosing through the solve


def test_golden_dosing_unit_solves_both_outlets_with_provenance_and_closed_form_nitrogen(client, dwsim):
    _, version = _publish(client)
    state = _draft(client.workspace, golden_ops(version, heater=False))
    assert not [item for item in state["findings"] if item["severity"] == "blocker"], state["findings"]
    run = _run(client.workspace, state)
    assert run["status"] == "completed", run.get("mixed_solve")
    studio = _studio(run)
    assert studio["version_id"] == version and studio["call_count"] == 1 and studio["cache_hits"] >= 0
    assert len(studio["source_sha256"]) == 64 and len(studio["contract_sha256"]) == 64
    assert run["units"]["Dosing"]["calculated"] is True and run["units"]["Dosing"]["owner"] == "jarvis_bio"
    assert {"Outlet", "Unused"} <= set(dwsim.flashes)  # both outlets went through the (fake) DWSIM flash
    flows = {tag: run["streams"][tag]["mass_flow_kg_s"] for tag in ("Culture", "Dose", "Outlet", "Unused")}
    assert flows["Outlet"] == pytest.approx(flows["Culture"] + 0.5 * flows["Dose"], rel=1e-12)
    assert flows["Unused"] == pytest.approx(0.5 * flows["Dose"], rel=1e-12)
    _assert_balances_closed(run)
    c, d, o = (run["culture"][tag]["values"]["nitrogen"]["mass_specific"] for tag in ("Culture", "Dose", "Outlet"))
    expected = (flows["Culture"] * c + 0.5 * flows["Dose"] * d) / (flows["Culture"] + 0.5 * flows["Dose"])
    assert o == pytest.approx(expected, rel=1e-9)


def test_changing_dose_split_changes_outlet_nitrogen_and_balances_still_close(client, dwsim):
    _, version = _publish(client)
    state = _draft(client.workspace, golden_ops(version, split=20.0, heater=False))
    low = _run(client.workspace, state)
    state = _patch(client.workspace, state, [SetUnitParams(op="set_unit_params", unit="dosing",
                                                           values={"dose_split": Q(value=90.0, unit="percent")})])
    high = _run(client.workspace, state)
    assert low["status"] == high["status"] == "completed"
    nitrogen = [run["culture"]["Outlet"]["values"]["nitrogen"]["mass_specific"] for run in (low, high)]
    assert nitrogen[1] > nitrogen[0]  # the dose is richer in nitrogen than the culture
    for run, share in ((low, 0.2), (high, 0.9)):
        flows = {tag: run["streams"][tag]["mass_flow_kg_s"] for tag in ("Culture", "Dose", "Outlet", "Unused")}
        assert flows["Outlet"] + flows["Unused"] == pytest.approx(flows["Culture"] + flows["Dose"], rel=1e-12)
        assert flows["Unused"] == pytest.approx((1 - share) * flows["Dose"], rel=1e-12)
        _assert_balances_closed(run)
    assert _studio(low)["call_count"] == _studio(high)["call_count"] == 1  # a fresh Process Run has a fresh cache

