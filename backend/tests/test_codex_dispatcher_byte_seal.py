from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISPATCHER = ROOT / "scripts" / "codex_result_delivery_dispatch.py"
EXPECTED_SHA256 = "9367b88fbba1cbd213a11b7ea00afceef682a2d10330becfa24f993382c75fda"


def test_codex_result_dispatcher_exact_bytes_are_reviewed_authority() -> None:
    assert DISPATCHER.is_file()
    assert hashlib.sha256(DISPATCHER.read_bytes()).hexdigest() == EXPECTED_SHA256
