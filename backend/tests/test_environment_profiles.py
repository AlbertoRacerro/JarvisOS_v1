from __future__ import annotations

import math
import socket
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from app.core.database import initialize_database
from app.core.paths import build_paths
from app.modules.environment import profiles
from app.modules.workspaces.models import WorkspaceCreate
from app.modules.workspaces.service import create_workspace


def _workspace() -> str:
    initialize_database()
    return create_workspace(WorkspaceCreate(name="Environment", slug="environment-test")).id


def _site(wid: str) -> dict[str, object]:
    return profiles.put_site(
        wid,
        {
            "name": "Boulder",
            "latitude": 39.742476,
            "longitude": -105.1786,
            "elevation_m": 1830.14,
            "timezone": "America/Denver",
            "water_body": "reservoir",
        },
        0,
    )


def test_site_validation_revision_cas_and_path_helpers() -> None:
    wid = _workspace()
    site = _site(wid)
    assert site["revision"] == 1
    with pytest.raises(profiles.EnvironmentError, match="conflict"):
        profiles.put_site(wid, site, 0)
    assert build_paths().environment_site_file(wid).is_file()
    with pytest.raises(profiles.EnvironmentError, match="latitude"):
        profiles.put_site(wid, {**site, "latitude": 91}, 1)
    with pytest.raises(profiles.EnvironmentError, match="IANA"):
        profiles.put_site(wid, {**site, "timezone": "No/Such_Zone"}, 1)


def test_profile_digest_immutability_verification_pages_and_bounds() -> None:
    wid = _workspace()
    profile = profiles.create_profile(
        wid,
        name="test",
        timestamps=["2026-01-01T00:15:00Z", "2026-01-01T00:30:00Z"],
        channels={"ghi": [0.0, 10.0], "cloud_cover": [None, 0.5]},
        resolution_minutes=15,
        provenance={"kind": "test"},
    )
    assert profile["profile_id"] == profile["digest"]
    duplicate = profiles.create_profile(
        wid,
        name="test",
        timestamps=["2026-01-01T00:15:00Z", "2026-01-01T00:30:00Z"],
        channels={"ghi": [0.0, 10.0], "cloud_cover": [None, 0.5]},
        resolution_minutes=15,
        provenance={"kind": "test"},
    )
    assert duplicate["profile_id"] == profile["profile_id"]
    assert profiles.read_profile(wid, profile["digest"], limit=1)["total"] == 2
    path = build_paths().environment_profiles_dir(wid) / (profile["digest"][7:] + ".json")
    with pytest.raises(FileExistsError):
        path.open("xb")
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(profiles.EnvironmentError, match="verification"):
        profiles.read_profile(wid, profile["digest"])
    with pytest.raises(profiles.EnvironmentError, match="ghi"):
        profiles.create_profile(
            wid,
            name="bad",
            timestamps=["2026-01-01T00:15:00Z"],
            channels={"ghi": [-1]},
            resolution_minutes=15,
            provenance={},
        )
    with pytest.raises(profiles.EnvironmentError, match="NaN"):
        profiles._canonical({"value": float("nan")})
    assert profiles._canonical({"x": -0.0}) == b'{"x":0}'


def test_profile_read_resolution_aggregation_and_paging() -> None:
    wid = _workspace()
    profile = profiles.create_profile(
        wid,
        name="aggregate",
        timestamps=["2026-01-01T00:15:00Z", "2026-01-01T00:30:00Z", "2026-01-01T00:45:00Z", "2026-01-01T01:00:00Z"],
        channels={"ghi": [0.0, 10.0, 20.0, 30.0], "air_temperature": [280.0, 281.0, 282.0, 283.0]},
        resolution_minutes=15,
        provenance={"kind": "test"},
    )
    coarse = profiles.read_profile(wid, profile["digest"], resolution_minutes=30, limit=1)
    assert coarse["resolution_minutes"] == 30
    assert coarse["total"] == 2
    assert coarse["timestamps"] == ["2026-01-01T00:30:00Z"]
    assert coarse["channels"]["ghi"] == [5.0]
    assert coarse["channels"]["air_temperature"] == [281.0]


def test_spa_reference_clear_sky_scaling_and_synthetic_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    wid = _workspace()
    _site(wid)
    position = profiles.spa_position("2003-10-17T12:30:30-07:00", 39.742476, -105.1786, 1830.14, 82000, 11, 67)
    assert position["apparent_zenith"] == pytest.approx(50.11162, abs=1e-4)
    assert position["azimuth"] == pytest.approx(194.34024, abs=1e-4)
    original_socket = socket.socket

    def blocked(*args: object, **kwargs: object) -> None:
        raise AssertionError("network socket creation attempted")

    monkeypatch.setattr(socket, "socket", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    start = "2026-06-21T04:00:00Z"
    generated = profiles.generate(
        wid,
        {
            "kind": "clear_sky",
            "name": "sky",
            "parameters": {"start": start, "count": 96, "resolution_minutes": 15, "clearness_factor": 1.0},
        },
    )
    half = profiles.generate(
        wid,
        {
            "kind": "clear_sky",
            "name": "half",
            "parameters": {"start": start, "count": 96, "resolution_minutes": 15, "clearness_factor": 0.5},
        },
    )
    values = profiles.read_profile(wid, generated["digest"])
    halves = profiles.read_profile(wid, half["digest"])
    assert all(values["channels"]["ghi"][i] == 0 for i in range(8))
    assert max(values["channels"]["ghi"]) > 0
    assert halves["channels"]["ghi"] == pytest.approx([v * 0.5 for v in values["channels"]["ghi"]])
    synthetic = profiles.generate(
        wid,
        {
            "kind": "synthetic_day",
            "name": "day",
            "parameters": {
                "start": start,
                "count": 96,
                "resolution_minutes": 15,
                "photoperiod": 12,
                "peak_par": 1500,
                "temperature_mean": 293.15,
                "temperature_amplitude": 5,
            },
        },
    )
    profile = profiles.read_profile(wid, synthetic["digest"])
    assert len(profile["channels"]["par"]) == 96
    assert original_socket


def test_csv_mapping_timezone_units_dst_and_linked_edits(tmp_path: Path) -> None:
    wid = _workspace()
    source = tmp_path / "tiny.csv"
    source.write_text("time,energy,temp\n2026-01-01 00:00,15,10\n2026-01-01 00:15,30,11\n", encoding="utf-8")
    created = profiles.confirm_csv(
        wid,
        source,
        "../tiny.csv",
        {
            "name": "mapped",
            "timestamp_column": "time",
            "timezone": "UTC",
            "resolution_minutes": 15,
            "stamp_convention": "start",
            "channels": {
                "ghi": {"column": "energy", "unit": "Wh m-2 interval-1"},
                "air_temperature": {"column": "temp", "unit": "°C"},
            },
        },
    )
    assert created["provenance"]["filename"] == "tiny.csv"
    values = profiles.read_profile(wid, created["digest"])
    assert values["channels"]["ghi"] == [60, 120]
    assert values["channels"]["air_temperature"] == pytest.approx([283.15, 284.15])
    edit = profiles.edit_profile(
        wid, created["digest"], {"operation": {"type": "cell", "channel": "ghi", "index": 0, "value": 75}}
    )
    assert edit["parent_digest"] == created["digest"]
    assert profiles.read_profile(wid, created["digest"])["channels"]["ghi"][0] == 60
    dst = tmp_path / "dst.csv"
    dst.write_text("time,value\n2026-11-01 01:30,4\n", encoding="utf-8")
    with pytest.raises(profiles.EnvironmentError, match="ambiguous"):
        profiles.confirm_csv(
            wid,
            dst,
            "dst.csv",
            {
                "timestamp_column": "time",
                "timezone": "America/Denver",
                "resolution_minutes": 60,
                "channels": {"ghi": {"column": "value"}},
            },
        )


def test_epw_and_pvgis_fixtures_normalize_time_and_preserve_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked(*args: object, **kwargs: object) -> None:
        raise AssertionError("network socket creation attempted during import")

    monkeypatch.setattr(socket, "socket", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    from app.modules.environment.routes import confirm

    wid = _workspace()
    _site(wid)
    fixtures = Path(__file__).parent / "fixtures" / "environment"
    stage_dir = build_paths().environment_staging_dir(wid)
    stage_dir.mkdir(parents=True, exist_ok=True)
    epw_id = "a" * 32
    (stage_dir / f"{epw_id}.stage").write_bytes((fixtures / "tiny.epw").read_bytes())
    epw = confirm(wid, epw_id, "folder\\tiny.epw", {"format": "epw"})
    values = profiles.read_profile(wid, epw["digest"])
    assert values["timestamps"] == [
        "2021-01-02T05:00:00Z",
        "2021-01-02T06:00:00Z",
        "2021-01-02T07:00:00Z",
    ]
    assert values["channels"]["ghi"] == [10.0, 0.0, 10.0]
    assert values["channels"]["air_temperature"][0] == pytest.approx(291.15)
    pvgis_id = "b" * 32
    (stage_dir / f"{pvgis_id}.stage").write_bytes((fixtures / "tiny-pvgis.csv").read_bytes())
    tmy = confirm(wid, pvgis_id, "tiny-pvgis.csv", {"format": "pvgis_tmy", "timezone": "UTC"})
    assert tmy["label"] == "representative year (TMY)"
    assert tmy["provenance"]["irradiance_time_offset"] == 0.5
    assert len(tmy["provenance"]["selected_month_year_pairs"]) == 12
    assert len(profiles.read_profile(wid, tmy["digest"], limit=5)["timestamps"]) == 5


def test_upload_stream_limit_extension_and_path_stripping() -> None:
    import asyncio

    from fastapi import HTTPException
    from starlette.requests import Request

    from app.modules.environment.routes import upload

    wid = _workspace()

    def request_for(chunks: list[bytes], headers: list[tuple[bytes, bytes]] | None = None) -> Request:
        pending = iter(chunks)

        async def receive() -> dict[str, object]:
            try:
                chunk = next(pending)
                return {"type": "http.request", "body": chunk, "more_body": True}
            except StopIteration:
                return {"type": "http.request", "body": b"", "more_body": False}

        return Request(
            {
                "type": "http",
                "asgi": {"version": "3.0"},
                "http_version": "1.1",
                "method": "POST",
                "scheme": "http",
                "path": "/",
                "raw_path": b"/",
                "query_string": b"",
                "headers": headers or [],
                "server": ("test", 80),
                "client": ("test", 123),
            },
            receive,
        )

    uploaded = asyncio.run(upload(wid, request_for([b"timestamp,value\n"]), "../../mapped.csv"))
    assert uploaded["filename"] == "mapped.csv"
    (build_paths().environment_staging_dir(wid) / f"{uploaded['upload_id']}.stage").unlink()
    with pytest.raises(HTTPException) as error:
        asyncio.run(upload(wid, request_for([b"x"], [(b"content-length", b"999999999")]), "x.csv"))
    assert error.value.status_code == 413
    with pytest.raises(HTTPException) as error:
        asyncio.run(upload(wid, request_for([b"x" * (20 * 1024 * 1024), b"y"]), "oversize.csv"))
    assert error.value.status_code == 413
    assert not list(build_paths().environment_staging_dir(wid).glob("*.stage"))
    with pytest.raises(HTTPException) as error:
        asyncio.run(upload(wid, request_for([b"x"]), "local.txt"))
    assert error.value.status_code == 400


def test_strict_elapsed_grid_limits_derived_par_and_107_matching_samples() -> None:
    wid = _workspace()
    _site(wid)
    with pytest.raises(profiles.EnvironmentError, match="resolution"):
        profiles.create_profile(
            wid, name="bad-step", timestamps=["2026-01-01T00:00:00Z"], channels={}, resolution_minutes=7, provenance={}
        )
    with pytest.raises(profiles.EnvironmentError, match="exact elapsed"):
        profiles.create_profile(
            wid,
            name="irregular",
            timestamps=["2026-01-01T00:00:00Z", "2026-01-01T00:16:00Z"],
            channels={"ghi": [0, 1]},
            resolution_minutes=15,
            provenance={},
        )
    with pytest.raises(profiles.EnvironmentError, match="250000"):
        profiles._validate({"timestamps": ["2026-01-01T00:00:00Z"] * 250001, "channels": {}})
    start = "2026-06-21T04:00:00Z"
    generated = profiles.generate(
        wid,
        {
            "kind": "clear_sky",
            "name": "sky",
            "parameters": {"start": start, "count": 96, "resolution_minutes": 15, "clearness_factor": 1},
        },
    )
    derived = profiles.derive_par(wid, generated["digest"])
    assert derived["label"] == "screening conversion"
    assert derived["parent_digest"] == generated["digest"]
    source_values = profiles.read_profile(wid, generated["digest"])
    derived_values = profiles.read_profile(wid, derived["digest"])
    assert derived_values["channels"]["par"] == [v * 2.06 for v in source_values["channels"]["ghi"]]
    params = {
        "start": start,
        "count": 96,
        "resolution_minutes": 15,
        "photoperiod": 12.0,
        "peak_par": 1500.0,
        "temperature_mean": 293.15,
        "temperature_amplitude": 5.0,
    }
    synthetic = profiles.generate(wid, {"kind": "synthetic_day", "name": "day", "parameters": params})
    values = profiles.read_profile(wid, synthetic["digest"])
    expected = []
    for stamp in values["timestamps"]:
        local = datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone(ZoneInfo("America/Denver"))
        hour = local.hour + local.minute / 60 + local.second / 3600
        sunrise = 12.0 - params["photoperiod"] / 2.0
        expected.append(
            params["peak_par"] * math.sin(math.pi * (hour - sunrise) / params["photoperiod"])
            if sunrise < hour < sunrise + params["photoperiod"]
            else 0.0
        )
    assert values["channels"]["par"] == expected
