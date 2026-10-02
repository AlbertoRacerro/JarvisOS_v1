"""Environment site, import, generator, and immutable profile API."""

from __future__ import annotations

import hashlib
import math
import time
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Query, Request

from app.core.paths import build_paths
from app.modules.environment import profiles as svc

router = APIRouter(prefix="/workspaces/{workspace_id}/environment", tags=["environment"])
STAGING_TTL_SECONDS = 24 * 60 * 60


def _cleanup_staging(root: Path) -> None:
    if not root.exists():
        return
    expiry = time.time() - STAGING_TTL_SECONDS
    for staged in root.glob("*.stage"):
        try:
            if staged.stat().st_mtime < expiry:
                staged.unlink()
        except FileNotFoundError:
            continue


def _error(exc: Exception) -> HTTPException:
    return HTTPException(status_code=409 if "conflict" in str(exc).lower() else 400, detail={"error": str(exc)})


@router.get("/site")
def get_site(workspace_id: str):
    try:
        return svc.get_site(workspace_id)
    except ValueError as e:
        raise _error(e) from e


@router.put("/site")
def put_site(workspace_id: str, payload: dict, expected_revision: int = Query(..., ge=0)):
    try:
        return svc.put_site(workspace_id, payload, expected_revision)
    except ValueError as e:
        raise _error(e) from e


@router.get("/profiles")
def list_profiles(workspace_id: str):
    try:
        return svc.list_profiles(workspace_id)
    except ValueError as e:
        raise _error(e) from e


@router.get("/profiles/{digest}")
def read_profile(
    workspace_id: str,
    digest: str,
    start: str | None = None,
    end: str | None = None,
    offset: int = 0,
    limit: int = 1000,
    resolution_minutes: int | None = Query(None),
):
    try:
        return svc.read_profile(workspace_id, digest, start, end, offset, limit, resolution_minutes)
    except ValueError as e:
        raise _error(e) from e


@router.post("/generate")
def generate(workspace_id: str, payload: dict):
    try:
        return svc.generate(workspace_id, payload)
    except (ValueError, KeyError, TypeError) as e:
        raise _error(e) from e


@router.post("/profiles/{digest}/derive-par")
def derive_par(workspace_id: str, digest: str, payload: dict):
    try:
        return svc.derive_par(workspace_id, digest, float(payload.get("factor", 2.06)), payload.get("name"))
    except (ValueError, KeyError, TypeError) as e:
        raise _error(e) from e


@router.post("/profiles/{digest}/edit")
def edit_profile(workspace_id: str, digest: str, payload: dict):
    try:
        return svc.edit_profile(workspace_id, digest, payload)
    except (ValueError, KeyError, TypeError, IndexError) as e:
        raise _error(e) from e


@router.post("/uploads")
async def upload(workspace_id: str, request: Request, filename: str):
    try:
        svc._workspace(workspace_id)
    except ValueError as e:
        raise _error(e) from e
    safe = Path(filename.replace("\\", "/")).name
    if Path(safe).suffix.lower() not in {".csv", ".epw"}:
        raise HTTPException(400, detail={"error": "Only .csv and .epw files are accepted."})
    length = request.headers.get("content-length")
    if length and (not length.isdigit() or int(length) > svc.MAX_UPLOAD):
        raise HTTPException(413, detail={"error": "Upload exceeds 20 MiB."})
    root = build_paths().environment_staging_dir(workspace_id)
    root.mkdir(parents=True, exist_ok=True)
    _cleanup_staging(root)
    token = uuid4().hex
    path = root / (token + ".stage")
    size = 0
    try:
        with path.open("xb") as stream:
            async for chunk in request.stream():
                size += len(chunk)
                if size > svc.MAX_UPLOAD:
                    raise HTTPException(413, detail={"error": "Upload exceeds 20 MiB."})
                stream.write(chunk)
        return {
            "upload_id": token,
            "filename": safe,
            "size": size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _stage(workspace_id: str, upload_id: str) -> Path:
    try:
        svc._workspace(workspace_id)
    except ValueError as e:
        raise _error(e) from e
    if not upload_id.isalnum() or len(upload_id) != 32:
        raise HTTPException(404, detail={"error": "Staged upload not found."})
    path = build_paths().environment_staging_dir(workspace_id) / (upload_id + ".stage")
    _cleanup_staging(path.parent)
    if not path.is_file():
        raise HTTPException(404, detail={"error": "Staged upload not found."})
    return path


@router.post("/uploads/{upload_id}/preview")
def preview(workspace_id: str, upload_id: str, filename: str):
    import pvlib

    path = _stage(workspace_id, upload_id)
    safe = Path(filename.replace("\\", "/")).name
    try:
        if safe.lower().endswith(".csv"):
            # PVGIS files are distinguished by their header, and parsed locally via pvlib.
            text = path.read_text("utf-8-sig", errors="replace")
            if "IRRADIANCE TIME OFFSET" in text[:2048].upper() or "LATITUDE (DECIMAL DEGREES)" in text[:2048].upper():
                data, meta = pvlib.iotools.read_pvgis_tmy(path, pvgis_format="csv")
                return {
                    "format": "pvgis_tmy",
                    "columns": list(data.columns),
                    "rows": data.head(5).reset_index().astype(str).values.tolist(),
                    "row_count": len(data),
                    "metadata": meta,
                }
            return {"format": "csv", "preview": svc.preview_csv(path)}
        data, meta = pvlib.iotools.read_epw(path)
        return {
            "format": "epw",
            "columns": list(data.columns),
            "rows": data.head(5).reset_index().astype(str).values.tolist(),
            "row_count": len(data),
            "metadata": meta,
        }
    except Exception as e:
        raise HTTPException(400, detail={"error": f"Import preview failed: {e}"}) from e


@router.post("/uploads/{upload_id}/confirm")
def confirm(workspace_id: str, upload_id: str, filename: str, payload: dict):
    import pandas as pd
    import pvlib

    path = _stage(workspace_id, upload_id)
    safe = Path(filename.replace("\\", "/")).name
    try:
        if safe.lower().endswith(".csv") and payload.get("format") != "pvgis_tmy":
            result = svc.confirm_csv(workspace_id, path, safe, payload["mapping"])
        elif safe.lower().endswith(".epw"):
            data, meta = pvlib.iotools.read_epw(path)
            index = data.index
            # EPW hour h labels the interval ending at h:00 local standard time; hour 24 rolls over.
            stamps = []
            for stamp in index:
                stamps.append((stamp.to_pydatetime() + timedelta(hours=1)).isoformat(timespec="minutes"))
            channels = {}
            for channel, col in (
                ("ghi", "ghi"),
                ("dni", "dni"),
                ("dhi", "dhi"),
                ("air_temperature", "temp_air"),
                ("wind_speed", "wind_speed"),
            ):
                if col in data.columns:
                    values = []
                    missing = {"ghi": 9999, "dni": 9999, "dhi": 9999, "air_temperature": 99.9, "wind_speed": 999}[
                        channel
                    ]
                    for value in data[col].tolist():
                        value = float(value)
                        values.append(
                            None
                            if not math.isfinite(value) or value == missing
                            else value + 273.15
                            if channel == "air_temperature"
                            else value
                        )
                    channels[channel] = values
            # EPW timestamps are local standard time with no DST; offset uses site's current standard offset.
            site = svc.get_site(workspace_id)
            if site is None:
                raise ValueError("Set a site timezone before importing EPW.")
            standard_offset = timezone(timedelta(hours=float(meta["TZ"])))
            tzstamp = []
            for raw in stamps:
                dt = datetime.fromisoformat(raw).replace(tzinfo=standard_offset, fold=0)
                tzstamp.append(dt.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"))
            result = svc.create_profile(
                workspace_id,
                name=str(payload.get("name") or safe),
                timestamps=tzstamp,
                channels=channels,
                resolution_minutes=60,
                provenance={
                    "kind": "import",
                    "filename": safe,
                    "original_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "format": "epw",
                    "column_mapping": "pvlib.read_epw",
                    "parser": "pvlib.iotools.read_epw",
                    "pvlib_version": pvlib.__version__,
                    "metadata": meta,
                },
            )
        elif payload.get("format") == "pvgis_tmy":
            data, meta = pvlib.iotools.read_pvgis_tmy(path, pvgis_format="csv")
            zone_name = str(payload.get("timezone") or "UTC")
            stamps = []
            for t in data.index:
                dt = t.to_pydatetime()
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=ZoneInfo(zone_name))
                stamps.append(dt.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"))
            mapping = {"ghi": "ghi", "dni": "dni", "dhi": "dhi", "temp_air": "air_temperature"}
            channels = {}
            for col, ch in mapping.items():
                if col in data:
                    vals = data[col].tolist()
                    channels[ch] = [
                        None if pd.isna(v) else float(v) + (273.15 if ch == "air_temperature" else 0) for v in vals
                    ]
            result = svc.create_profile(
                workspace_id,
                name=str(payload.get("name") or safe),
                timestamps=stamps,
                channels=channels,
                resolution_minutes=60,
                provenance={
                    "kind": "import",
                    "filename": safe,
                    "original_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "format": "pvgis_tmy",
                    "parser": "pvlib.iotools.read_pvgis_tmy",
                    "pvlib_version": pvlib.__version__,
                    "metadata": meta,
                    "selected_month_year_pairs": meta.get("months_selected"),
                    "irradiance_time_offset": meta.get("inputs", {}).get("irradiance time offset"),
                },
                profile_label="representative year (TMY)",
            )
        else:
            raise ValueError("Unsupported import confirmation format.")
        path.unlink(missing_ok=True)
        return result
    except (ValueError, KeyError, TypeError) as e:
        raise _error(e) from e
