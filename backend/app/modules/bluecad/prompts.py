"""Versioned prompt templates for the BLUECAD AI loop."""

from __future__ import annotations

import json
from typing import Any

PROMPT_VERSION = "bluecad_ai_loop_v0_stage1"

SYSTEM_TEMPLATE = """You generate BLUECAD GeometrySpec v0 JSON only.
Allowed part kinds: tube_run, bend, joint.
Each part must include a declared block with expected deterministic quantities.
Use port composition rules from GeometrySpec v0: named ports connect compatible tube interfaces, and transforms are explicit.
Return exactly one JSON object, optionally inside a fenced json block. Do not include prose, markdown explanations, proprietary formulas, or BlueRev parameters.
"""


def generate_prompt(brief_text: str) -> str:
    return f"{SYSTEM_TEMPLATE}\nDesign brief:\n{brief_text}\n"


def repair_prompt(failing_spec: dict[str, Any], validation_report: dict[str, Any]) -> str:
    return (
        f"{SYSTEM_TEMPLATE}\nRepair this GeometrySpec using only the failing spec and validation report.\n"
        "Failing spec JSON:\n"
        f"{json.dumps(failing_spec, sort_keys=True)}\n"
        "Validation report JSON:\n"
        f"{json.dumps(validation_report, sort_keys=True)}\n"
    )
