from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from cloud_delivery_bridge import MARKER, BridgeError, parse_payload  # noqa: E402
from repository_delivery import DeliveryRefusal  # noqa: E402


def _body(path: str) -> str:
    patch = f"diff --git a/{path} b/{path}\n"
    metadata = {
        "version": 1,
        "pr": 633,
        "base_sha": "a" * 40,
        "target_ref": "fixture/codex-result-authority",
        "patch_sha256": hashlib.sha256(patch.encode("utf-8")).hexdigest(),
        "changed_paths": [path],
        "validation_profile": "docs",
    }
    return (
        f"{MARKER}\n```json\n{json.dumps(metadata)}\n```\n"
        f"```diff\n{patch}\n```"
    )


def test_codex_transport_refuses_agents_at_repository_safety_boundary() -> None:
    with pytest.raises(DeliveryRefusal, match="sensitive repository path refused: AGENTS.md"):
        parse_payload(_body("AGENTS.md"))


@pytest.mark.parametrize(
    "path",
    [
        "docs/ARCHITECTURE.md",
        "docs/DECISIONS.md",
        "docs/AGENT_EXECUTION_AND_AUTOMATION_PROTOCOL.md",
        "docs/COORDINATION_BUS_V2.md",
        "docs/POST_112_PARALLEL_DELIVERY_PROFILE.md",
        "docs/specs/STATUS.md",
        "docs/specs/114-readiness-2026-08-31.md",
        "docs/specs/999-future-authority.md",
    ],
)
def test_codex_transport_refuses_canonical_authority_classes(path: str) -> None:
    with pytest.raises(BridgeError, match="bridge/control path refused"):
        parse_payload(_body(path))


def test_codex_transport_still_allows_non_authority_docs() -> None:
    payload = parse_payload(_body("docs/runbooks/operator-note.md"))
    assert payload.changed_paths == ("docs/runbooks/operator-note.md",)
    assert payload.validation_profile == "docs"
