"""Immutable workspace environment profiles and offline generators."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.database import open_sqlite_connection
from app.core.paths import build_paths
from app.modules.events.service import utc_now

MAX_UPLOAD = 20 * 1024 * 1024
MAX_POINTS = 250_000
MAX_SECONDS = 2 * 366 * 86400
PARSER_VERSION = "jarvis-environment-csv/1"
CHANNELS = {
    "ghi": ("W m-2", "energy"),
    "dni": ("W m-2", "energy"),
    "dhi": ("W m-2", "energy"),
    "par": ("umol m-2 s-1", "nonnegative"),
    "air_temperature": ("K", "temperature"),
    "sea_temperature": ("K", "temperature"),
    "wind_speed": ("m s-1", "nonnegative"),
    "cloud_cover": ("1", "fraction"),
    "wave_height": ("m", "nonnegative"),
    "wave_period": ("s", "nonnegative"),
}
STEP_MINUTES = {5, 10, 15, 30, 60, 1440}


class EnvironmentError(ValueError):
    pass


def _canonical(value: Any) -> bytes:
    def number(value: int | float) -> str:
        if isinstance(value, int):
            return str(value)
        if not math.isfinite(value):
            raise EnvironmentError("Canonical profile content cannot contain NaN or Infinity.")
        if value == 0:
            return "0"
        raw = repr(value).lower()
        decimal = Decimal(raw)
        magnitude = abs(value)
        if 1e-6 <= magnitude < 1e21:
            result = format(decimal, "f")
            if "." in result:
                result = result.rstrip("0").rstrip(".")
        else:
            mantissa, exponent = raw.split("e") if "e" in raw else (raw, "0")
            mantissa = mantissa.rstrip("0").rstrip(".") if "." in mantissa else mantissa
            exp = int(exponent)
            result = mantissa + "e" + ("+" if exp >= 0 else "") + str(exp)
        return result

    def clean(x: Any) -> Any:
        if isinstance(x, float):
            if not math.isfinite(x):
                raise EnvironmentError("Canonical profile content cannot contain NaN or Infinity.")
            return 0 if x == 0 else x
        if isinstance(x, dict):
            return {str(k): clean(v) for k, v in x.items()}
        if isinstance(x, list):
            return [clean(v) for v in x]
        return x

    def encode(x: Any) -> str:
        x = clean(x)
        if x is None:
            return "null"
        if x is True:
            return "true"
        if x is False:
            return "false"
        if isinstance(x, (int, float)):
            return number(x)
        if isinstance(x, str):
            return json.dumps(x, ensure_ascii=False, separators=(",", ":"))
        if isinstance(x, list):
            return "[" + ",".join(encode(item) for item in x) + "]"
        if isinstance(x, dict):
            keys = sorted(x, key=lambda key: str(key).encode("utf-16be"))
            return "{" + ",".join(encode(str(key)) + ":" + encode(x[key]) for key in keys) + "}"
        raise EnvironmentError(f"Unsupported canonical JSON value: {type(x).__name__}.")

    return encode(value).encode("utf-8")


def _workspace(wid: str) -> None:
    with open_sqlite_connection() as db:
        if db.execute("SELECT 1 FROM workspaces WHERE id=?", (wid,)).fetchone() is None:
            raise EnvironmentError("Workspace not found.")


def get_site(wid: str) -> dict[str, Any] | None:
    _workspace(wid)
    p = build_paths().environment_site_file(wid)
    return json.loads(p.read_text("utf-8")) if p.exists() else None


def put_site(wid: str, payload: dict[str, Any], expected_revision: int) -> dict[str, Any]:
    _workspace(wid)
    site = {k: payload.get(k) for k in ("name", "latitude", "longitude", "elevation_m", "timezone", "water_body")}
    if not isinstance(site["name"], str) or not site["name"].strip():
        raise EnvironmentError("Site name is required.")
    if site["water_body"] is not None and not isinstance(site["water_body"], str):
        raise EnvironmentError("water_body must be a text label or null.")
    for key, lo, hi in (("latitude", -90, 90), ("longitude", -180, 180)):
        x = site[key]
        if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or not lo <= x <= hi:
            raise EnvironmentError(f"{key} must be in [{lo}, {hi}].")
    x = site["elevation_m"]
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        raise EnvironmentError("elevation_m must be finite.")
    try:
        ZoneInfo(str(site["timezone"]))
    except (ZoneInfoNotFoundError, TypeError):
        raise EnvironmentError("timezone must be a valid IANA timezone.") from None
    p = build_paths().environment_site_file(wid)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open_sqlite_connection() as db:
        db.execute("BEGIN IMMEDIATE")
        old = json.loads(p.read_text("utf-8")) if p.exists() else None
        rev = old["revision"] if old else 0
        if rev != expected_revision:
            raise EnvironmentError(f"Site revision conflict: expected {expected_revision}, current {rev}.")
        result = {**site, "revision": rev + 1}
        tmp = p.with_name(f".{p.name}.{uuid4().hex}.tmp")
        tmp.write_bytes(_canonical(result))
        tmp.replace(p)
        db.commit()
    return result


def _stamp(value: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as e:
        raise EnvironmentError(f"Invalid timestamp {value!r}.") from e
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise EnvironmentError(f"Timestamp {value!r} requires an explicit UTC offset or timezone.")
    return dt.astimezone(UTC)


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or int(value) != value:
        raise EnvironmentError(f"{label} must be an integer.")
    return int(value)


def _validate(profile: dict[str, Any]) -> None:
    stamps = profile.get("timestamps")
    if not isinstance(stamps, list) or not stamps or len(stamps) > MAX_POINTS:
        raise EnvironmentError(f"Profile must contain 1 to {MAX_POINTS} timestamps.")
    times = [_stamp(s) for s in stamps]
    if any(a >= b for a, b in zip(times, times[1:], strict=False)):
        raise EnvironmentError("Timestamps must be strictly increasing in UTC.")
    if (times[-1] - times[0]).total_seconds() > MAX_SECONDS:
        raise EnvironmentError("Profile span cannot exceed two years.")
    step = profile.get("resolution_minutes")
    if step is not None:
        if step not in STEP_MINUTES:
            raise EnvironmentError("resolution_minutes must be 5, 10, 15, 30, 60 or 1440.")
        if any((b - a).total_seconds() != step * 60 for a, b in zip(times, times[1:], strict=False)):
            raise EnvironmentError("Timestamps must use the declared exact elapsed resolution.")
    for name, values in profile.get("channels", {}).items():
        if name not in CHANNELS or not isinstance(values, list) or len(values) != len(stamps):
            raise EnvironmentError(f"Invalid channel {name!r} or column length.")
        kind = CHANNELS[name][1]
        for stamp, v in zip(stamps, values, strict=True):
            if v is None:
                continue
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                raise EnvironmentError(f"{name} at {stamp}: value must be finite or null.")
            bad = (
                (kind == "temperature" and not 200 <= v <= 350)
                or (kind == "fraction" and not 0 <= v <= 1)
                or (kind in {"nonnegative", "energy"} and v < 0)
            )
            if bad:
                raise EnvironmentError(f"{name} at {stamp}: value violates channel bounds.")


def create_profile(
    wid: str,
    *,
    name: str,
    timestamps: list[str],
    channels: dict[str, list[float | None]],
    resolution_minutes: int | None,
    provenance: dict[str, Any],
    parent_digest: str | None = None,
    profile_label: str | None = None,
) -> dict[str, Any]:
    _workspace(wid)
    timestamps = [_stamp(stamp).isoformat().replace("+00:00", "Z") for stamp in timestamps]
    profile = {
        "name": name,
        "timestamps": timestamps,
        "channels": channels,
        "units": {k: CHANNELS[k][0] for k in channels},
        "resolution_minutes": resolution_minutes,
        "start": timestamps[0] if timestamps else None,
        "end": timestamps[-1] if timestamps else None,
        "parent_digest": parent_digest,
        "provenance": provenance,
        "label": profile_label,
    }
    _validate(profile)
    content = _canonical(profile)
    root = build_paths().environment_profiles_dir(wid)
    root.mkdir(parents=True, exist_ok=True)
    temporary = root / (".profile-" + uuid4().hex + ".tmp")
    hasher = hashlib.sha256()
    try:
        with temporary.open("xb") as stream:
            for offset in range(0, len(content), 64 * 1024):
                chunk = content[offset : offset + 64 * 1024]
                stream.write(chunk)
                hasher.update(chunk)
            stream.flush()
            os.fsync(stream.fileno())
        digest = "sha256:" + hasher.hexdigest()
        path = root / (digest[7:] + ".json")
        try:
            os.link(temporary, path)
        except FileExistsError:
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest[7:]:
                raise EnvironmentError("Existing immutable profile blob failed digest verification.") from None
    finally:
        temporary.unlink(missing_ok=True)
    aid = str(uuid4())
    now = utc_now()
    with open_sqlite_connection() as db:
        db.execute(
            "INSERT INTO artifacts (id,workspace_id,filename,stored_path,artifact_type,mime_type,sha256,source_ref,status,created_at,notes) VALUES (?,?,?,?, 'environment_profile','application/json',?,?,'registered',?,?)",
            (aid, wid, path.name, str(path), digest[7:], digest, now, name),
        )
        db.commit()
    return {"profile_id": digest, "digest": digest, "artifact_id": aid, **profile}


def _read(wid: str, digest: str) -> dict[str, Any]:
    _workspace(wid)
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise EnvironmentError("Invalid profile digest.")
    p = build_paths().environment_profiles_dir(wid) / (digest[7:] + ".json")
    try:
        content = p.read_bytes()
    except OSError as e:
        raise EnvironmentError("Profile not found.") from e
    if hashlib.sha256(content).hexdigest() != digest[7:]:
        raise EnvironmentError("Profile digest verification failed.")
    return json.loads(content)


def list_profiles(wid: str) -> list[dict[str, Any]]:
    _workspace(wid)
    root = build_paths().environment_profiles_dir(wid)
    out = []
    if root.exists():
        for p in sorted(root.glob("*.json"), reverse=True):
            d = "sha256:" + p.stem
            try:
                item = _read(wid, d)
            except EnvironmentError:
                continue
            out.append(
                {
                    "profile_id": d,
                    "digest": d,
                    "name": item["name"],
                    "channels": item["units"],
                    "start": item["start"],
                    "end": item["end"],
                    "resolution_minutes": item["resolution_minutes"],
                    "provenance": item["provenance"],
                    "parent_digest": item["parent_digest"],
                    "label": item.get("label"),
                }
            )
    return out


def read_profile(
    wid: str,
    digest: str,
    start: str | None = None,
    end: str | None = None,
    offset: int = 0,
    limit: int = 1000,
    resolution_minutes: int | None = None,
) -> dict[str, Any]:
    item = _read(wid, digest)
    indexes = [
        i
        for i, s in enumerate(item["timestamps"])
        if (start is None or _stamp(s) >= _stamp(start)) and (end is None or _stamp(s) <= _stamp(end))
    ]
    timestamps = [item["timestamps"][i] for i in indexes]
    columns = {k: [v[i] for i in indexes] for k, v in item["channels"].items()}
    base_resolution = item["resolution_minutes"]
    result_resolution = resolution_minutes or base_resolution
    if resolution_minutes is not None:
        if resolution_minutes not in STEP_MINUTES or base_resolution is None or resolution_minutes < base_resolution:
            raise EnvironmentError("Requested read resolution must be an allowed step at least as coarse as the profile.")
        if resolution_minutes % base_resolution:
            raise EnvironmentError("Requested read resolution must be a multiple of the profile resolution.")
        factor = resolution_minutes // base_resolution
        if factor > 1:
            grouped_stamps: list[str] = []
            grouped_columns: dict[str, list[float | None]] = {k: [] for k in columns}
            for first in range(0, len(timestamps), factor):
                last = min(len(timestamps), first + factor)
                grouped_stamps.append(timestamps[last - 1])
                for name, values in columns.items():
                    group = values[first:last]
                    if any(value is None for value in group):
                        grouped_columns[name].append(None)
                    elif CHANNELS[name][1] == "energy":
                        grouped_columns[name].append(sum(group) / len(group))
                    else:
                        grouped_columns[name].append(group[-1])
            timestamps, columns = grouped_stamps, grouped_columns
    total = len(timestamps)
    page = slice(max(0, offset), max(0, offset) + min(max(1, limit), 5000))
    return {
        **item,
        "profile_id": digest,
        "digest": digest,
        "timestamps": timestamps[page],
        "channels": {k: v[page] for k, v in columns.items()},
        "resolution_minutes": result_resolution,
        "offset": max(0, offset),
        "total": total,
    }


def _grid(start: str, count: int, step: int) -> list[datetime]:
    if step not in STEP_MINUTES:
        raise EnvironmentError("resolution_minutes must be 5, 10, 15, 30, 60 or 1440.")
    if not 1 <= count <= MAX_POINTS:
        raise EnvironmentError("Invalid point count.")
    first = _stamp(start)
    return [first + timedelta(minutes=step * (i + 1)) for i in range(count)]


def spa_position(
    timestamp: str,
    latitude: float,
    longitude: float,
    elevation_m: float,
    pressure_pa: float = 82_000.0,
    temperature_c: float = 11.0,
    delta_t: float = 67.0,
) -> dict[str, float]:
    import pandas as pd
    import pvlib

    time = pd.DatetimeIndex([_stamp(timestamp)])
    result = pvlib.solarposition.spa_python(
        time,
        latitude,
        longitude,
        altitude=elevation_m,
        pressure=pressure_pa,
        temperature=temperature_c,
        delta_t=delta_t,
    ).iloc[0]
    return {
        "apparent_zenith": float(result["apparent_zenith"]),
        "azimuth": float(result["azimuth"]),
    }


def generate(wid: str, payload: dict[str, Any]) -> dict[str, Any]:
    site = get_site(wid)
    if site is None:
        raise EnvironmentError("Set the workspace site before generating profiles.")
    kind = payload.get("kind")
    p = payload.get("parameters", {})
    if not isinstance(p, dict):
        raise EnvironmentError("Generator parameters must be an object.")
    step = _integer(p.get("resolution_minutes", 60), "resolution_minutes")
    count = _integer(p.get("count", 24), "count")
    times = _grid(str(p.get("start")), count, step)
    snap = {k: site[k] for k in ("name", "latitude", "longitude", "elevation_m", "timezone", "water_body")}
    channels: dict[str, list[float | None]]
    if kind == "synthetic_day":
        photo = float(p["photoperiod"])
        peak = float(p["peak_par"])
        mean = float(p["temperature_mean"])
        amp = float(p["temperature_amplitude"])
        if not 0 < photo <= 24 or not math.isfinite(peak) or peak < 0 or not all(map(math.isfinite, (mean, amp))):
            raise EnvironmentError(
                "synthetic_day requires photoperiod in (0, 24], nonnegative peak PAR, and finite temperatures."
            )
        sunrise = 12 - photo / 2
        zone = ZoneInfo(site["timezone"])
        par: list[float | None] = []
        temp: list[float | None] = []
        for t in times:
            local = t.astimezone(zone)
            hour = local.hour + local.minute / 60 + local.second / 3600
            par.append(peak * math.sin(math.pi * (hour - sunrise) / photo) if sunrise < hour < sunrise + photo else 0.0)
            temp.append(mean + amp * math.sin(2 * math.pi * (hour - 9) / 24))
        channels = {"par": par, "air_temperature": temp}
    elif kind == "clear_sky":
        import pandas as pd
        import pvlib

        idx = pd.DatetimeIndex(times)
        loc = pvlib.location.Location(site["latitude"], site["longitude"], site["timezone"], site["elevation_m"])
        solar_position = pvlib.solarposition.spa_python(
            idx,
            site["latitude"],
            site["longitude"],
            altitude=site["elevation_m"],
        )
        weather = loc.get_clearsky(idx, model="ineichen", solar_position=solar_position)
        factor = float(p.get("clearness_factor", 1))
        if not math.isfinite(factor) or not 0 <= factor <= 1:
            raise EnvironmentError("clearness_factor must be in [0, 1].")
        channels = {
            key: [max(0, float(v) * factor) for v in weather[col].tolist()]
            for key, col in (("ghi", "ghi"), ("dni", "dni"), ("dhi", "dhi"))
        }
    else:
        raise EnvironmentError("Unknown generator kind.")
    stamps = [x.isoformat(timespec="seconds").replace("+00:00", "Z") for x in times]
    return create_profile(
        wid,
        name=str(payload.get("name") or kind),
        timestamps=stamps,
        channels=channels,
        resolution_minutes=step,
        provenance={
            "kind": kind,
            "parameters": p,
            "site_snapshot": snap,
            "pvlib_version": __import__("pvlib").__version__ if kind == "clear_sky" else None,
        },
    )


def derive_par(wid: str, digest: str, factor: float = 2.06, name: str | None = None) -> dict[str, Any]:
    s = _read(wid, digest)
    if "ghi" not in s["channels"] or not math.isfinite(factor) or factor <= 0:
        raise EnvironmentError("A positive conversion factor and GHI channel are required.")
    c = {**s["channels"], "par": [None if v is None else v * factor for v in s["channels"]["ghi"]]}
    return create_profile(
        wid,
        name=name or f"{s['name']} · derived PAR",
        timestamps=s["timestamps"],
        channels=c,
        resolution_minutes=s["resolution_minutes"],
        provenance={
            "kind": "derived_par",
            "source_digest": digest,
            "factor_umol_per_j": factor,
            "label": "screening conversion",
        },
        parent_digest=digest,
        profile_label="screening conversion",
    )


def edit_profile(wid: str, digest: str, payload: dict[str, Any]) -> dict[str, Any]:
    s = _read(wid, digest)
    c = {k: list(v) for k, v in s["channels"].items()}
    op = payload.get("operation", {})
    if not isinstance(op, dict):
        raise EnvironmentError("Edit operation must be an object.")
    name = str(op.get("channel", ""))
    if name not in c:
        raise EnvironmentError("Edit channel not found.")
    if op.get("type") == "cell":
        index = _integer(op["index"], "edit index")
        if not 0 <= index < len(c[name]):
            raise EnvironmentError("Edit index is outside the profile.")
        c[name][index] = op.get("value")
    elif op.get("type") in {"scale", "offset"}:
        raw_value = op.get("value")
        if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)) or not math.isfinite(raw_value):
            raise EnvironmentError("Edit value must be finite and numeric.")
        value = float(raw_value)
        for i, stamp in enumerate(s["timestamps"]):
            if op.get("start") and _stamp(stamp) < _stamp(op["start"]):
                continue
            if op.get("end") and _stamp(stamp) > _stamp(op["end"]):
                continue
            if c[name][i] is not None:
                c[name][i] = c[name][i] * value if op["type"] == "scale" else c[name][i] + value
    else:
        raise EnvironmentError("Unknown edit operation.")
    return create_profile(
        wid,
        name=str(payload.get("name") or f"{s['name']} · edited"),
        timestamps=s["timestamps"],
        channels=c,
        resolution_minutes=s["resolution_minutes"],
        provenance={"kind": "edit", "summary": op},
        parent_digest=digest,
    )


def preview_csv(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if len(rows) < 2:
        raise EnvironmentError("CSV line 1: expected a header and at least one row.")
    return {"columns": rows[0], "rows": rows[1:6], "row_count": len(rows) - 1, "parser": PARSER_VERSION}


def confirm_csv(wid: str, path: Path, filename: str, m: dict[str, Any]) -> dict[str, Any]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        cols = reader.fieldnames or []
    tc = m.get("timestamp_column")
    if tc not in cols:
        raise EnvironmentError("CSV column mapping: timestamp column not found.")
    stamps = []
    zone = ZoneInfo(str(m["timezone"])) if m.get("timezone") else None
    for line, row in enumerate(rows, 2):
        raw = row.get(tc, "")
        try:
            try:
                dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except ValueError:
                dt = datetime.strptime(raw, str(m.get("timestamp_format") or "%Y-%m-%d %H:%M:%S"))
            if dt.tzinfo is None:
                if zone is None:
                    raise EnvironmentError(f"CSV line {line}: naive timestamp needs an IANA timezone.")
                a, b = dt.replace(tzinfo=zone, fold=0), dt.replace(tzinfo=zone, fold=1)
                if a.astimezone(UTC).astimezone(zone).replace(tzinfo=None) != dt:
                    raise EnvironmentError(f"CSV line {line}: ambiguous or nonexistent DST timestamp.")
                if a.utcoffset() != b.utcoffset():
                    fold = m.get("fold")
                    if fold not in (0, 1):
                        raise EnvironmentError(
                            f"CSV line {line}: ambiguous DST timestamp needs an explicit fold mapping."
                        )
                    a = dt.replace(tzinfo=zone, fold=fold)
                dt = a
            stamps.append(dt.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"))
        except EnvironmentError:
            raise
        except (ValueError, TypeError) as e:
            raise EnvironmentError(f"CSV line {line}: invalid timestamp in column {tc!r}.") from e
    step = _integer(m.get("resolution_minutes", 60), "resolution_minutes")
    if m.get("stamp_convention", "end") not in {"start", "end"}:
        raise EnvironmentError("CSV mapping stamp_convention must be start or end.")
    if m.get("stamp_convention") == "start":
        stamps = [
            (_stamp(s) + timedelta(minutes=step)).isoformat(timespec="seconds").replace("+00:00", "Z") for s in stamps
        ]
    channels = {}
    for channel, spec in m.get("channels", {}).items():
        col = spec.get("column")
        if channel not in CHANNELS or col not in cols:
            raise EnvironmentError(f"CSV mapping: invalid column for {channel}.")
        unit = spec.get("unit", CHANNELS[channel][0])
        allowed_units = {CHANNELS[channel][0]}
        if channel in {"ghi", "dni", "dhi"}:
            allowed_units.add("Wh m-2 interval-1")
        if channel in {"air_temperature", "sea_temperature"}:
            allowed_units.add("°C")
        if unit not in allowed_units:
            raise EnvironmentError(f"CSV mapping: unsupported unit {unit!r} for {channel}.")
        values = []
        for line, row in enumerate(rows, 2):
            raw = row.get(col, "").strip()
            try:
                v = None if raw in {"", "null", "NA"} else float(raw)
            except ValueError as e:
                raise EnvironmentError(f"CSV line {line}, column {col!r}: invalid number.") from e
            if channel in {"ghi", "dni", "dhi"} and unit == "Wh m-2 interval-1":
                v = None if v is None else v * 60 / step
            elif channel in {"air_temperature", "sea_temperature"} and unit == "°C":
                v = None if v is None else v + 273.15
            values.append(v)
        channels[channel] = values
    return create_profile(
        wid,
        name=str(m.get("name") or Path(filename).name),
        timestamps=stamps,
        channels=channels,
        resolution_minutes=step,
        provenance={
            "kind": "import",
            "filename": Path(filename).name,
            "original_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "format": "csv",
            "column_mapping": m,
            "parser": PARSER_VERSION,
        },
    )
