"""Spec 165 host proof: hand a real BLUECAD 3MF to Windows through explorer.exe.

Run on the WSL qualification host, outside jarvis-sandbox (the sandbox hides
/mnt/c, wslpath and WSL interop), from a checkout of the 165 branch:

    cd backend && .venv/bin/python ../scripts/165-print-handoff-host-proof.py /mnt/c/Users/<you>/JarvisOS-print

It uses a fresh temporary JARVISOS_DATA_ROOT, builds the deterministic tube
template, calls the real open-in-slicer endpoint with the flag on and prints
the event row. Windows then opens the file with the default .3mf program.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

TUBE = {"template": "tube", "params": {"outer_d_mm": 40.0, "wall_t_mm": 3.0, "length_mm": 120.0}}


def main() -> int:
    from fastapi.testclient import TestClient

    from app.core.bootstrap import initialize_storage
    from app.main import create_app

    initialize_storage(seed_default=True)
    with TestClient(create_app()) as client:
        workspace = client.get("/workspaces").json()[0]["id"]
        print("capability", client.get(f"/workspaces/{workspace}/bluecad/print-handoff/capability").json())
        candidate = client.post(f"/workspaces/{workspace}/bluecad/candidates/from-template", json=TUBE).json()
        aggregate = client.get(f"/workspaces/{workspace}/bluecad/candidates/{candidate['id']}/aggregate").json()
        artifact = next((item for item in aggregate["exports"] if item["roles"][0] == "export.3mf"), None)
        if artifact is None:
            print("no 3MF export; candidate", candidate.get("status"), candidate.get("parked_reason"))
            return 1
        response = client.post(f"/workspaces/{workspace}/bluecad/artifacts/{artifact['id']}/open-in-slicer")
        print("open-in-slicer", response.status_code, json.dumps(response.json(), indent=2))
        return 0 if response.status_code == 200 else 1


# Build workers spawn children that re-import this module; only the parent runs the proof.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
if __name__ == "__main__":
    if len(sys.argv) != 2 or not sys.argv[1].startswith("/mnt/"):
        sys.exit("usage: 165-print-handoff-host-proof.py /mnt/<drive>/<directory>")
    Path(sys.argv[1]).mkdir(parents=True, exist_ok=True)
    os.environ.update(
        JARVISOS_DATA_ROOT=tempfile.mkdtemp(prefix="jarvis-165-host-"),
        JARVISOS_PRINT_HANDOFF_ENABLED="1",
        JARVISOS_PRINT_HANDOFF_DIR=sys.argv[1],
    )
    sys.exit(main())
