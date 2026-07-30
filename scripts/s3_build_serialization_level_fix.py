from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "backend/app/modules/bluecad/evidence_egress.py"
TEST = ROOT / "backend/tests/bluecad/test_evidence_egress.py"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one replacement, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    CODE,
    '''import json
from collections.abc import Iterator
''',
    '''import json
import re
from collections.abc import Iterator
''',
)

replace_once(
    CODE,
    '''        ordered_source_refs=ordered_source_refs,
    )
''',
    '''        ordered_source_refs=ordered_source_refs,
        effective_levels=effective_levels,
    )
''',
)

replace_once(
    CODE,
    '''        or _contains_json_structure(content)
        or "RAW_GEOMETRY_SPEC_BEGIN" in content
''',
    '''        or _contains_json_structure(content)
        or _contains_serialized_geometry_authority(content, forbidden_spec_json)
        or "RAW_GEOMETRY_SPEC_BEGIN" in content
''',
)

replace_once(
    CODE,
    '''def _contains_json_structure(content: str) -> bool:
    decoder = json.JSONDecoder()
    for index, character in enumerate(content):
        if character not in "[{":
            continue
        try:
            value, _ = decoder.raw_decode(content[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, (dict, list)):
            return True
    return False


def _canonical_derivative_row(workspace_id: str, derivative_id: str) -> dict[str, Any]:
''',
    '''def _contains_json_structure(content: str) -> bool:
    decoder = json.JSONDecoder()
    for index, character in enumerate(content):
        if character not in "[{":
            continue
        try:
            value, _ = decoder.raw_decode(content[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, (dict, list)):
            return True
    return False


def _contains_serialized_geometry_authority(
    content: str,
    forbidden_spec_json: str,
) -> bool:
    """Reject raw GeometrySpec key/value authority independent of serialization."""

    try:
        forbidden = json.loads(forbidden_spec_json)
    except json.JSONDecodeError as exc:  # server-owned canonical JSON must be valid
        raise sensitivity.SensitivityPolicyError(
            "Server GeometrySpec authority is malformed."
        ) from exc
    lines = tuple(content.splitlines())
    for key, value in _iter_geometry_scalar_pairs(forbidden):
        key_pattern = re.compile(
            rf"(?i)(?<![A-Za-z0-9_]){re.escape(key)}(?![A-Za-z0-9_])"
        )
        for line in lines:
            match = key_pattern.search(line)
            if match is None:
                continue
            tail = line[match.end() : match.end() + 160]
            if _serialized_tail_contains_value(tail, value):
                return True
    identifiers = _geometry_identifier_values(forbidden)
    return any(
        re.search(
            rf"(?i)(?<![A-Za-z0-9_]){re.escape(identifier)}(?![A-Za-z0-9_])",
            content,
        )
        is not None
        for identifier in identifiers
    )


def _iter_geometry_scalar_pairs(value: Any) -> Iterator[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                yield from _iter_geometry_scalar_pairs(item)
            elif item is not None:
                yield str(key), item
    elif isinstance(value, list):
        for item in value:
            yield from _iter_geometry_scalar_pairs(item)


def _serialized_tail_contains_value(tail: str, value: Any) -> bool:
    tail = tail.lstrip(" \\t'\"")
    if tail.startswith((":", "=")):
        tail = tail[1:].lstrip()
    elif tail and not tail[0].isspace():
        return False
    if isinstance(value, bool):
        return re.search(rf"(?i)^['\"]?{str(value).lower()}(?![A-Za-z0-9_])", tail) is not None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        number = re.match(r"^[\s'\"]*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)", tail)
        if number is None:
            return False
        try:
            return float(number.group(1)) == float(value)
        except ValueError:
            return False
    expected = str(value).strip().casefold()
    if not expected:
        return False
    candidate = tail.lstrip(" \\t'\"").casefold()
    return candidate.startswith(expected) and (
        len(candidate) == len(expected)
        or not candidate[len(expected)].isalnum()
        and candidate[len(expected)] != "_"
    )


def _geometry_identifier_values(value: Any) -> tuple[str, ...]:
    identifiers: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).casefold()
            if (
                isinstance(item, str)
                and len(item.strip()) >= 3
                and (
                    normalized in {"id", "name", "ref", "label"}
                    or normalized.endswith(("_id", "_name", "_ref"))
                )
            ):
                identifiers.add(item.strip())
            identifiers.update(_geometry_identifier_values(item))
    elif isinstance(value, list):
        for item in value:
            identifiers.update(_geometry_identifier_values(item))
    return tuple(sorted(identifiers))


def _canonical_derivative_row(workspace_id: str, derivative_id: str) -> dict[str, Any]:
''',
)

replace_once(
    CODE,
    '''    sight: EvidenceSight,
    ordered_source_refs: tuple[str, ...],
) -> dict[str, Any]:
''',
    '''    sight: EvidenceSight,
    ordered_source_refs: tuple[str, ...],
    effective_levels: tuple[str, ...],
) -> dict[str, Any]:
''',
)

replace_once(
    CODE,
    '''        "ordered_source_refs": list(ordered_source_refs),
        "sight_digest": sight.digest,
''',
    '''        "ordered_source_refs": list(ordered_source_refs),
        "effective_levels": list(effective_levels),
        "sight_digest": sight.digest,
''',
)

replace_once(
    TEST,
    '''        'Generic repair\\n{"objects":[{"id":"tube-1","diameter":0.4}]}',
''',
    '''        'Generic repair\\n{"objects":[{"id":"tube-1","diameter":0.4}]}',
        "Generic repair\\nschema_version: geometry_spec_v0_1",
        "Generic repair\\n{'schema_version': 'geometry_spec_v0_1'}",
        "Generic repair\\nschema_version=geometry_spec_v0_1",
''',
)

replace_once(
    TEST,
    '''        "ordered_source_refs": ["evidence:e1"],
        "sight_digest": "sha256:" + "1" * 64,
''',
    '''        "ordered_source_refs": ["evidence:e1"],
        "effective_levels": ["S2"],
        "sight_digest": "sha256:" + "1" * 64,
''',
)

replace_once(
    TEST,
    '''        dict(base, ordered_source_refs=["evidence:e2", "evidence:e1"]),
    )
''',
    '''        dict(base, ordered_source_refs=["evidence:e2", "evidence:e1"]),
        dict(base, effective_levels=["S3"]),
    )
''',
)

with TEST.open("a", encoding="utf-8") as handle:
    handle.write(
        '''


def test_renderer_context_binds_ordered_effective_levels() -> None:
    sight = EvidenceSight(
        text="EVIDENCE_SIGHT_V0\\nevidence:e1",
        digest="sha256:" + "1" * 64,
        record_ids=("e1",),
    )
    s2 = evidence_egress_module._renderer_config_context(
        workspace_id=WORKSPACE_ID,
        candidate_id="candidate-1",
        source_attempt_id="attempt-1",
        sight=sight,
        ordered_source_refs=("evidence:e1",),
        effective_levels=("S2",),
    )
    s3 = evidence_egress_module._renderer_config_context(
        workspace_id=WORKSPACE_ID,
        candidate_id="candidate-1",
        source_attempt_id="attempt-1",
        sight=sight,
        ordered_source_refs=("evidence:e1",),
        effective_levels=("S3",),
    )

    assert s2["effective_levels"] == ["S2"]
    assert s3["effective_levels"] == ["S3"]
    assert s2 != s3
'''
    )

print("S3 serialization and level-binding patch prepared")
