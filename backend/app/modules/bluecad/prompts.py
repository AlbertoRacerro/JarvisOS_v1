"""Versioned prompt templates for the BLUECAD AI loop.

The system template must give the model the exact GeometrySpec v0 structure and
a concrete valid example: the schema is strict (additionalProperties: false,
const/enum fields, exact param names), so a model without an example cannot
produce a passing spec. Contains no BlueRev formulas or proprietary parameters
(layering rule).
"""

from __future__ import annotations

import json
from typing import Any

PROMPT_VERSION = "bluecad_ai_loop_v2"

SYSTEM_TEMPLATE = """You output exactly one BLUECAD GeometrySpec v0 JSON object and nothing else.
No prose, no explanation. A single JSON object, optionally wrapped in one ```json fenced block.

UNITS: millimetres and radians. "OD 10 cm" means outer_d 100. "length 3 m" means length 3000.

STRUCTURE (all field names are exact; NO extra fields are allowed anywhere -- adding any
field not listed here makes the output invalid):
{
  "spec_version": "bluecad_geometry_spec_v0_1",   // exactly this string, required
  "name": "<short name>",                          // optional
  "parts": [ ... ],                                // required, at least one part
  "connections": [ ... ],                          // optional; omit or [] for a single part
  "declared": { ... }                              // OPTIONAL -- omit unless you are confident
}

PART KINDS (each part: {"part_id": "<unique id>", "kind": "...", "params": {...}, "frame": {...}}).
Use ONLY these kinds and ONLY the params listed for each; no other kinds or params exist:
- tube_run       params: {"outer_d": >0, "wall_t": >0 (< outer_d/2), "length": >0}
                 ports: port_a, port_b
- bend           params: {"outer_d": >0, "wall_t": >0 (< outer_d/2), "bend_radius": >0, "angle": >0 rad}
                 ports: port_a, port_b
- joint          params: {"joint_type": "socket", "outer_d": >0, "wall_t": >0, "socket_len": >0}
                 ports: port_a, port_b
- manifold       params: {"outer_d_main": >0, "wall_t": >0, "length": >0, "n_out": 1..12 int,
                 "out_d": >0, "out_wall_t": >0, "spacing": >0}   ports: in_a, in_b, out_1..out_n
- float          params: {"outer_d": >0, "length": >0, "n_mounts": 1..12 int, "pad_d": >0}
                 ports: mount_1..mount_n
- anchor_mount   params: {"base_w": >0, "base_l": >0, "base_t": >0, "eye_d": >0}   port: mount_a
- harvest_module params: {"outer_d": >0, "height": >0, "wall_t": >0, "port_d": >0}
                 ports: in_a, out_a, drain_a
"frame" is optional: {"origin": [x,y,z], "direction": [x,y,z]} (a non-zero direction). Omit for defaults.

PORTS & CONNECTIONS: a connection joins two ports:
{"from": "<part_id>.<port>", "to": "<other_id>.<port>"}.
Two connected TUBE ports (port_a/port_b/in_*/out_*) must have matching outer_d and wall_t.
PAD ports (mount_*) connect only to other pad ports with matching pad_d.
Do NOT specify transforms -- placement is computed from the connections.

DEGRADE GRACEFULLY -- this is critical:
- The brief may ask for things this vocabulary cannot express: materials, colours,
  "transparent", surface finish, motion, "slides along", kinematics, sensors, labels.
  IGNORE every non-geometric attribute. Model only the static shape with the kinds above.
- If a requested feature has no matching kind, approximate it with the closest available
  kind, or omit that part. NEVER invent a new kind or a new param name to fit the words --
  an invented field is rejected and your whole output fails.
- When unsure, produce the simplest valid geometry that captures the load-bearing intent.

DECLARED (optional): {"total_volume_mm3": {"value": <num>, "rel_tol": <num> 0..1},
"bbox_mm": {"min": [x,y,z], "max": [x,y,z], "abs_tol": <num>}, "min_wall_t": <num>}.
Only include declared if you can compute it; omitting it is safe and preferred when unsure.

EXAMPLE -- a single 1 m tube, outer_d 100, wall_t 5 (no declared block):
{"spec_version": "bluecad_geometry_spec_v0_1", "name": "single_tube",
 "parts": [{"part_id": "t1", "kind": "tube_run", "params": {"outer_d": 100.0, "wall_t": 5.0, "length": 1000.0}}],
 "connections": []}

EXAMPLE -- a tube then a 90 degree bend, connected:
{"spec_version": "bluecad_geometry_spec_v0_1", "name": "tube_and_bend",
 "parts": [
   {"part_id": "t1", "kind": "tube_run", "params": {"outer_d": 110.0, "wall_t": 4.0, "length": 600.0}},
   {"part_id": "b1", "kind": "bend", "params": {"outer_d": 110.0, "wall_t": 4.0, "bend_radius": 400.0, "angle": 1.5708}}
 ],
 "connections": [{"from": "t1.port_b", "to": "b1.port_a"}]}
"""


def generate_prompt(brief_text: str) -> str:
    return f"{SYSTEM_TEMPLATE}\nDesign brief:\n{brief_text}\n\nReturn the GeometrySpec v0 JSON object now."


def repair_prompt(failing_spec: dict[str, Any], validation_report: dict[str, Any]) -> str:
    return (
        f"{SYSTEM_TEMPLATE}\n"
        "Your previous GeometrySpec failed validation. Fix it using only the failing spec and the "
        "validation report below. Change the minimum needed to make failing checks pass; keep valid "
        "parts unchanged. Return one corrected GeometrySpec v0 JSON object.\n"
        "Failing spec JSON:\n"
        f"{json.dumps(failing_spec, sort_keys=True)}\n"
        "Validation report JSON:\n"
        f"{json.dumps(validation_report, sort_keys=True)}\n"
    )
