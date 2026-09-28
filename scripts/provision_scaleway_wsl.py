#!/usr/bin/env python3
"""Windows-only one-time DPAPI to WSL encrypted credential importer."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    if os.name != "nt":
        print("Run this importer with Windows Python in the DPAPI owner's account.", file=sys.stderr)
        return 1
    repo = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo / "backend"))
    from app.modules.secrets.storage import ScalewaySecretStore

    persisted = ScalewaySecretStore().read()
    if persisted.state != "usable" or not persisted.value:
        print("Scaleway DPAPI credential is not usable.", file=sys.stderr)
        return 1
    distro = os.environ.get("JARVISOS_WSL_DISTRO", "Ubuntu-24.04")
    account = os.environ.get("JARVISOS_WSL_USER", "thera")
    helper = f"/home/{account}/src/JarvisOS_v1/scripts/wsl_encrypt_credential.py"
    result = subprocess.run(
        ["wsl.exe", "-d", distro, "-u", "root", "--", "/usr/bin/python3", helper,
         account, "SCALEWAY_API_KEY"],
        input=persisted.value.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode:
        print("Scaleway WSL provisioning failed; no plaintext credential was stored.", file=sys.stderr)
        return 1
    status = result.stdout.decode("utf-8", errors="replace").strip()
    if status not in {"provisioned; protection=host", "provisioned; protection=host+tpm2"}:
        print("Scaleway WSL provisioning returned an unexpected status.", file=sys.stderr)
        return 1
    print(status)
    return 0


if __name__ == "__main__":
    sys.exit(main())
