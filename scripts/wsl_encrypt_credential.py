#!/usr/bin/env python3
"""Root-side, one-time stdin to systemd encrypted credential provisioning."""

from __future__ import annotations

import os
import pwd
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path


def provision(account: str, name: str) -> str:
    if os.geteuid() != 0 or not re.fullmatch(r"[A-Z][A-Z0-9_]*", name):
        raise RuntimeError("provisioning_precondition_failed")
    user = pwd.getpwnam(account)
    directory = Path(user.pw_dir) / ".config" / "jarvisos" / "credentials.encrypted"
    for parent in (Path(user.pw_dir), directory.parent.parent, directory.parent):
        if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
            raise RuntimeError("credential_directory_invalid")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    metadata = directory.lstat()
    if not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid not in {0, user.pw_uid}:
        raise RuntimeError("credential_directory_invalid")
    os.chown(directory, user.pw_uid, user.pw_gid)
    os.chmod(directory, 0o700)
    target = directory / name
    if os.path.lexists(target):
        raise RuntimeError("credential_already_provisioned")

    has_tpm = subprocess.run(
        ["/usr/bin/systemd-creds", "--quiet", "has-tpm2"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0
    protection = "host+tpm2" if has_tpm else "host"
    descriptor, temporary_name = tempfile.mkstemp(prefix=".credential-", dir=directory)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        result = subprocess.run(
            ["/usr/bin/systemd-creds", "--quiet", f"--with-key={protection}",
             f"--name={name}", "encrypt", "-", str(temporary)],
            stdin=sys.stdin.buffer,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode != 0 or temporary.stat().st_size == 0:
            raise RuntimeError("credential_encryption_failed")
        os.chown(temporary, user.pw_uid, user.pw_gid)
        os.chmod(temporary, 0o600)
        os.link(temporary, target, follow_symlinks=False)
    finally:
        temporary.unlink(missing_ok=True)
    return protection


if __name__ == "__main__":
    try:
        if len(sys.argv) != 3:
            raise RuntimeError("provisioning_arguments_invalid")
        mode = provision(sys.argv[1], sys.argv[2])
    except (RuntimeError, OSError, KeyError) as exc:
        print(str(exc) if isinstance(exc, RuntimeError) else "credential_provisioning_failed", file=sys.stderr)
        sys.exit(1)
    print(f"provisioned; protection={mode}")
